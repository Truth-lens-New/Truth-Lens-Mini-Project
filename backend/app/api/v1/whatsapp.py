"""
WhatsApp Webhook API

Handles incoming text and media messages from Twilio WhatsApp Sandbox,
features an interactive menu, and uses BackgroundTasks for the V3 Engine!
"""
import os
import traceback
import httpx
import asyncio
from fastapi import APIRouter, Request, Form, Response, BackgroundTasks
from twilio.rest import Client

from app.services import analyze_image_for_deepfake

# V3 Architecture imports
from app.api.v3.endpoints.analyze import InputType
from app.services.input import InputGateway
from app.services.extraction import ClaimExtractorV3
from app.services.typing import ClaimClassifier

router = APIRouter(prefix="/api/v1/webhook", tags=["Webhook"])

# Twilio Config
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = "whatsapp:+14155238886"

# In-memory session store (Phone Number -> State)
# States: None (Menu), "AWAITING_TEXT", "AWAITING_MEDIA"
user_sessions = {}

# Lazy init V3 services
_input_gateway = None
_claim_extractor = None
_claim_classifier = None
_verdict_engine = None
_normalizer = None

def get_v3_services():
    global _input_gateway, _claim_extractor, _claim_classifier, _verdict_engine, _normalizer
    if _input_gateway is None:
        _input_gateway = InputGateway()
        _claim_extractor = ClaimExtractorV3()
        _claim_classifier = ClaimClassifier()
        from app.services.investigation import get_verdict_engine
        _verdict_engine = get_verdict_engine()
        from app.services.normalization.normalizer import get_normalizer
        _normalizer = get_normalizer()
    return _input_gateway, _claim_extractor, _claim_classifier, _verdict_engine, _normalizer

def send_whatsapp_async(to_number: str, text: str):
    """Pushes a message back to the user asynchronously using Twilio REST API"""
    try:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            print("Missing Twilio Keys in .env!")
            return
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(from_=TWILIO_NUMBER, body=text, to=to_number)
    except Exception as e:
        print(f"Failed to send async WhatsApp message: {e}")

async def process_media_background(media_url: str, content_type: str, from_number: str):
    """Background task to download and analyze media for deepfakes"""
    message = ""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(media_url)
            if response.status_code == 200:
                media_bytes = response.content
                
                # Run deepfake detection
                result = await analyze_image_for_deepfake(media_bytes, content_type=content_type)
                
                verdict = result["verdict"]
                confidence = result.get("confidence_level", "medium").upper()
                evidence_list = result.get("evidence", [])
                
                # Format bullet points
                evidence_str = ""
                for ev in evidence_list[:3]:
                    evidence_str += f"• {ev}\n"
                if not evidence_str:
                    evidence_str = "No deepfake traces found."
                
                emoji = "📸"
                verdict_emoji = "🛑" if verdict == "FAKE" else "✅"
                
                message = f"*TruthLens Media Analysis*\n\n{emoji} *Processing:* {content_type}\n\n{verdict_emoji} *Verdict:* {verdict}\n*Confidence:* {confidence}\n\n*Forensic Evidence:*\n{evidence_str}"
            else:
                message = "⚠️ Could not download the media from WhatsApp."
    except Exception as e:
        print(f"Media bg logic error: {e}")
        traceback.print_exc()
        message = "⚠️ Sorry, TruthLens encountered a media processing error."
        
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_whatsapp_async, from_number, message)


async def process_text_background(text: str, from_number: str):
    """Background task to analyze text claims using V3 Engine"""
    message = ""
    try:
        input_gateway, extractor, classifier, engine, normalizer = get_v3_services()
        
        input_type = InputType.URL if text.startswith("http") else InputType.TEXT
        processed = input_gateway.process(input_type, text)
        
        if input_type == InputType.URL:
            raw_claims = extractor.extract_crux(processed)
        else:
            raw_claims = extractor.extract(processed)
            
        if not raw_claims:
            message = "⚠️ No checkable claims detected in your message."
        else:
            primary_claim = raw_claims[0]
            
            norm = normalizer.normalize(primary_claim.text)
            primary_claim.canonical_id = norm['canonical_id']
            
            cached_result = None
            if norm['is_duplicate'] and norm.get('cached_result'):
                cached_result = norm['cached_result']
                
            typed_claims = classifier.classify([primary_claim])
            typed_claim = typed_claims[0]
            
            if cached_result:
                result = cached_result
            else:
                result = await engine.verify(typed_claim)
                if result.verdict.value != "not_checkable":
                    normalizer.update_result(typed_claim.canonical_id, result)
            
            emoji = "✅" if result.verdict.value == "REAL" else "🛑" if result.verdict.value == "FAKE" else "⚠️"
            sources_str = f"(Checked {result.sources_checked} verified sources)" if hasattr(result, 'sources_checked') else ""
            
            message = (
                f"🚀 *TruthLens V3 Analysis*\n\n"
                f"*Claim:* \"{result.original_text}\"\n\n"
                f"{emoji} *Verdict:* {result.verdict.value.upper()}\n"
                f"*Confidence:* {round(result.confidence * 100)}%\n\n"
                f"*Investigation Summary* {sources_str}:\n"
                f"{result.evidence_summary[:700]}..."
            )
    except Exception as e:
        print(f"Text bg logic error: {e}")
        traceback.print_exc()
        message = "⚠️ Sorry, TruthLens V3 encountered an error processing your claim."
        
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_whatsapp_async, from_number, message)


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    Body: str = Form(None),
    From: str = Form(...),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None)
):
    """
    Interactive WhatsApp Webhook.
    Replies immediately with a Loading/Menu state, and defers heavy processing.
    """
    text = Body.strip() if Body else ""
    user_state = user_sessions.get(From, "MENU")
    
    # Check for reset/menu command
    if text.lower() in ["hi", "hello", "menu", "help", "reset"]:
        user_state = "MENU"
        
    reply_message = ""

    if user_state == "MENU":
        if text == "1":
            user_sessions[From] = "AWAITING_TEXT"
            reply_message = "📝 Please send me the *text claim* or *news article URL* you want to fact-check!"
        elif text == "2":
            user_sessions[From] = "AWAITING_MEDIA"
            reply_message = "📸 Please send me the *image* or *video* you suspect might be a deepfake!"
        else:
            # Show Main Menu
            reply_message = (
                "👋 *Welcome to TruthLens!*\n"
                "What would you like to verify today?\n\n"
                "Reply with a number:\n"
                "1️⃣ *Fact Check* (Text / Links)\n"
                "2️⃣ *Deepfake Check* (Images / Video)\n"
            )

    elif user_state == "AWAITING_TEXT":
        if NumMedia > 0:
            reply_message = "⚠️ You sent media, but I'm expecting text! Please send a text claim, or reply 'menu' to go back."
        elif not text:
            reply_message = "⚠️ Please send a valid text claim."
        else:
            # Start background processing
            background_tasks.add_task(process_text_background, text, From)
            reply_message = "⏳ *TruthLens V3 is analyzing this...* Please give me 5-15 seconds to research verified sources!"
            user_sessions[From] = "MENU"

    elif user_state == "AWAITING_MEDIA":
        if NumMedia > 0 and MediaUrl0:
            background_tasks.add_task(process_media_background, MediaUrl0, MediaContentType0, From)
            reply_message = "⏳ *Analyzing media forensics...* Please wait while the deepfake model runs."
            user_sessions[From] = "MENU"
        else:
            reply_message = "⚠️ You didn't attach any media! Please send a photo/video, or reply 'menu' to go back."

    # Return immediate TwiML XML
    xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_message}</Message>
</Response>'''
    
    return Response(content=xml_response, media_type="application/xml")
