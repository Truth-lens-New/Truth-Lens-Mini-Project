"""
TruthLens WhatsApp Bot — Twilio Webhook

Handles inbound WhatsApp messages asynchronously to avoid 15s Twilio timeouts.
- Interactive Menu (1, 2, 3)
- Text → claim verification pipeline (/api/v1/analyze)
- Image → deepfake detection (/api/v1/analyze-media)
- Chat → Lensy Support Chatbot
"""

import httpx
from fastapi import APIRouter, Form, Request, Response, BackgroundTasks
from typing import Optional

from app.core.config import settings
from app.services.chatbot import generate_chat_response
from app.services import (
    extract_claims,
    search_factchecks,
    search_news,
    classify_all_stances,
    weighted_stance,
    aggregate_verdict,
    generate_explanation,
    llm_assess_claim,
    analyze_image_for_deepfake,
)

router = APIRouter(prefix="/api/v1", tags=["WhatsApp"])

# ── In-Memory Session State ────────────────────────────────────────────────

# Maps phone numbers to their current state dictionary
# Example: {"whatsapp:+12345": {"mode": "menu", "chat_history": []}}
SESSION_STATE = {}

# ── Helpers ────────────────────────────────────────────────────────────────

def twiml_reply(body: str) -> Response:
    """Return an immediate Twilio MessagingResponse XML reply."""
    safe = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>{safe}</Message>
</Response>"""
    return Response(content=xml, media_type="text/xml")


async def send_whatsapp_message(to_number: str, body: str):
    """Send an async WhatsApp message via Twilio REST API to the user."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    data = {
        "To": to_number,
        "From": settings.twilio_whatsapp_from,
        "Body": body
    }
    auth = (settings.twilio_account_sid, settings.twilio_auth_token)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, auth=auth, data=data)
            resp.raise_for_status()
            print(f"[Twilio] Message sent to {to_number}: {body[:50]}...")
    except Exception as e:
        print(f"[Twilio Error] Failed to send message to {to_number}: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"[Twilio Error Details] {e.response.text}")


def verdict_emoji(verdict: str) -> str:
    v = str(verdict).lower()
    if "true" in v or "support" in v:
        return "✅"
    if "false" in v or "refut" in v or "mislead" in v:
        return "❌"
    if "mixed" in v or "uncertain" in v:
        return "⚠️"
    return "🔍"


MENU_TEXT = """🦉 *TruthLens Main Menu*

Please reply with a number:

1️⃣ Verify a Text Claim
2️⃣ Deepfake Analysis (Send an Image)
3️⃣ Talk to Lensy the Owl Support 🦉

_(Type *menu* at any time to return here)_"""


# ── Webhook endpoint ────────────────────────────────────────────────────────

@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    Body: Optional[str] = Form(default=""),
    NumMedia: Optional[int] = Form(default=0),
    MediaUrl0: Optional[str] = Form(default=None),
    MediaContentType0: Optional[str] = Form(default=None),
    From: Optional[str] = Form(default=""),
):
    """
    Twilio WhatsApp inbound webhook. Replies instantly using TwiML and 
    dispatches expensive pipelines to BackgroundTasks.
    """
    sender = From
    body = (Body or "").strip()

    # Initialize state
    if sender not in SESSION_STATE:
        SESSION_STATE[sender] = {"mode": "menu", "chat_history": []}
        
    state = SESSION_STATE[sender]

    # ── Exit / Reset to Menu ─────────────────────────────────────────────
    if body.lower() in ("menu", "exit", "quit", "help", "hi", "hello"):
        state["mode"] = "menu"
        state["chat_history"] = []
        return twiml_reply(MENU_TEXT)

    # ── Handle Modes ─────────────────────────────────────────────────────
    
    # 1. MENU MODE
    if state["mode"] == "menu":
        if body == "1":
            state["mode"] = "text"
            return twiml_reply("📝 *Text Verification*\n\nPlease send me the claim, rumor, or news headline you'd like me to investigate!")
        elif body == "2":
            state["mode"] = "media"
            return twiml_reply("🖼 *Deepfake Analysis*\n\nPlease send me the image you'd like me to scan for manipulation.")
        elif body == "3":
            state["mode"] = "chat"
            return twiml_reply("🦉 *Hoot hoot! I am Lensy!*\n\nI'm the official TruthLens support owl. Ask me anything about how to use the app, deepfake detection, or fact-checking! ✨\n\n_(Type *menu* to exit at any time)_")
        else:
            # Fallback: if they just send random media while in menu, auto-trigger deepfake
            if NumMedia and NumMedia > 0 and MediaUrl0:
                 state["mode"] = "menu" # reset to menu for next time
                 background_tasks.add_task(_process_image_bg, MediaUrl0, MediaContentType0 or "image/jpeg", sender)
                 return twiml_reply("⏳ Thanks! Running deepfake detection on your image. This takes about 10-15 seconds...\n\n_I'll reply here as soon as the results are ready._")
            
            return twiml_reply("🤔 I didn't quite catch that.\n\n" + MENU_TEXT)

    # 2. TEXT VERIFICATION MODE
    elif state["mode"] == "text":
        background_tasks.add_task(_process_text_claim_bg, body, sender)
        state["mode"] = "menu" # Return to menu after submission
        return twiml_reply("⏳ Investigating your claim across live sources, fact-checking databases, and AI models. This takes up to 30 seconds...\n\n_I'll ping you with the full report shortly!_")

    # 3. MEDIA VERIFICATION MODE
    elif state["mode"] == "media":
        if NumMedia and NumMedia > 0 and MediaUrl0:
            background_tasks.add_task(_process_image_bg, MediaUrl0, MediaContentType0 or "image/jpeg", sender)
            state["mode"] = "menu" # Return to menu after submission
            return twiml_reply("⏳ Thanks! Running deepfake detection on your image. This takes about 10-15 seconds...\n\n_I'll reply here as soon as the results are ready._")
        else:
            return twiml_reply("⚠️ Please send an actual image file for analysis. (Type *menu* to cancel)")

    # 4. LENSY CHATBOT MODE
    elif state["mode"] == "chat":
        # Add user message to history
        state["chat_history"].append({"role": "user", "content": body})
        
        # Keep history from growing unbounded (prevent context explosion for long sessions)
        if len(state["chat_history"]) > 20: 
            state["chat_history"] = state["chat_history"][-20:]
            
        # Lensy resolves fast enough (2-4s) that we can reply inline without timeouts
        try:
            response_text = await generate_chat_response(state["chat_history"])
            state["chat_history"].append({"role": "model", "content": response_text})
        except Exception:
            response_text = "I'm having a little trouble connecting to my systems right now! 🦉 Please try again."

        return twiml_reply(response_text)

    # Fallback safety net
    state["mode"] = "menu"
    return twiml_reply(MENU_TEXT)


# ── Background Processors ───────────────────────────────────────────────────

async def _process_text_claim_bg(claim: str, to_number: str):
    """Run full fact-check pipeline in background and send progressive WhatsApp push replies."""
    try:
        await send_whatsapp_message(to_number, "⏳ *Step 1/4* | _Breaking down your claim..._")
        claim_result = await extract_claims(claim)
        primary_claim = claim_result.get("primary_claim") or claim[:500]

        await send_whatsapp_message(to_number, "🔍 *Step 2/4* | _Searching fact-check databases..._")
        factcheck = await search_factchecks(primary_claim)
        
        await send_whatsapp_message(to_number, "🌐 *Step 3/4* | _Gathering global news sources..._")
        articles = await search_news(primary_claim, max_results=5)
        
        await send_whatsapp_message(to_number, "🤖 *Step 4/4* | _AI analyzing semantic stances..._")
        articles_with_stance = await classify_all_stances(primary_claim, articles)
        stance_summary = weighted_stance(articles_with_stance)

        verdict_result = aggregate_verdict(
            factcheck_result=factcheck,
            stance_summary=stance_summary,
            domain_trust={"score": "unknown"},
        )

        if verdict_result.get("basis") in ("insufficient_evidence", "mixed_evidence"):
            llm = await llm_assess_claim(primary_claim)
            if llm.get("used") and llm.get("verdict"):
                verdict_result = {
                    "verdict": llm["verdict"],
                    "confidence": llm.get("confidence", "medium"),
                    "basis": "llm_assessment",
                }

        await send_whatsapp_message(to_number, "✅ _Finalizing executive summary..._")
        explanation = await generate_explanation({
            "claim": primary_claim,
            "verdict": verdict_result["verdict"],
            "confidence": verdict_result["confidence"],
            "factcheck": factcheck,
            "stance_summary": stance_summary,
            "domain_trust": {"score": "unknown"},
        })

        verdict = verdict_result["verdict"]
        confidence = verdict_result["confidence"]
        emoji = verdict_emoji(verdict)

        counts = stance_summary.get("counts", {})
        supports = counts.get("SUPPORTS", 0)
        refutes = counts.get("REFUTES", 0)
        discuss = counts.get("DISCUSS", 0)
        unrelated = counts.get("UNRELATED", 0)
        total_sources = supports + refutes + discuss + unrelated

        short_explanation = explanation[:800] + "..." if len(explanation) > 800 else explanation

        fact_line = ""
        if factcheck.get("found") and factcheck.get("rating"):
            fact_line = f"\n🏷 *Official Fact-check:* _{factcheck['rating']}_ \n🔗 *Source:* {factcheck.get('source','')}"

        reply = (
            f"*{claim[:100]}...*\n\n"
            f"{emoji} *VERDICT: {verdict.upper()}*\n"
            f"📊 *Confidence:* {confidence}\n"
            f"🗞 *Sources Evaluated:* {total_sources} "
            f"({supports} support | {refutes} refute | {discuss} discuss)\n"
            f"{fact_line}\n\n"
            f"📋 *Executive Summary*\n{short_explanation}"
        )

        await send_whatsapp_message(to_number, reply)

    except Exception as e:
        await send_whatsapp_message(to_number, f"⚠️ *Error analysing claim:*\n_{str(e)[:200]}_\n\nPlease try again in a moment.")


async def _process_image_bg(media_url: str, content_type: str, to_number: str):
    """Download image, run deepfake detection, and send progressive WhatsApp push replies."""
    try:
        await send_whatsapp_message(to_number, "📥 _Downloading media securely..._")
        
        # Download the image from Twilio
        auth = (settings.twilio_account_sid, settings.twilio_auth_token)
        # Twilio sends a 307 redirect to S3 for media, must follow redirects
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(media_url, auth=auth)
            resp.raise_for_status()
            image_bytes = resp.content

        await send_whatsapp_message(to_number, "🧠 _Scanning with forensics AI model..._")
        
        # Run deepfake detection
        result = await analyze_image_for_deepfake(image_bytes, content_type=content_type)

        verdict = result.get("verdict", "UNKNOWN").upper()
        confidence = round(result.get("confidence", 0))
        fake_pct = round(result.get("fake_probability", 0))
        real_pct = round(result.get("real_probability", 0))
        model = result.get("model", "EfficientNet-B0")
        evidence = result.get("evidence", [])

        is_fake = verdict == "FAKE"
        emoji = "🔴" if is_fake else "🟢"
        
        bullets = ""
        if evidence:
            bullets = "\n".join(f"• {e}" for e in evidence[:4])
            bullets = f"\n\n🔬 *Forensic Indicators*\n{bullets}"

        reply = (
            f"🖼 *TruthLens Deepfake Analysis*\n"
            f"└ _Model: {model}_\n\n"
            f"{emoji} *VERDICT: {verdict}*\n"
            f"Confidence: {confidence}%\n\n"
            f"📊 *Probability Breakdown*\n"
            f"├ FAKE: {fake_pct}%\n"
            f"└ REAL: {real_pct}%"
            f"{bullets}"
        )

        await send_whatsapp_message(to_number, reply)

    except httpx.HTTPError as e:
        await send_whatsapp_message(to_number, f"⚠️ *Error: Could not download the image.*\n_{str(e)[:150]}_")
    except Exception as e:
        await send_whatsapp_message(to_number, f"⚠️ *Error analysing image:*\n_{str(e)[:200]}_\n\nPlease try again.")
