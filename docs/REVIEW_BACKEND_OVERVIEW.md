# Backend Review Notes

This is the high-level backend flow for TruthLens.

## 1) App Boot and Routing

Source: `backend/app/main.py`

```python
app = FastAPI(
    title="TruthLens API",
    description="Misinformation analysis and claim verification API",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(analyze_router)   # v1
app.include_router(history_router)   # v1 history
app.include_router(v3_router)        # v3 analyze/investigate
```

What to say:
- FastAPI app starts DB on lifespan startup.
- We keep legacy v1 endpoints and newer v3 pipeline side-by-side.

## 2) v3 Endpoint Shape

Source: `backend/app/api/v3/endpoints/analyze.py`

```python
@router.post("/analyze", response_model=AnalyzeResponseV3)
def analyze_content(request: AnalyzeRequestV3):
    processed = input_gateway.process(input_type, request.content)
    raw_claims = claim_extractor.extract(processed)
    typed_claims = claim_classifier.classify(raw_claims)
    ...
```

```python
@router.post("/investigate", response_model=InvestigateResponseV3)
async def investigate_content(...):
    ...
    typed_claims = await run_in_threadpool(claim_classifier.classify, raw_claims)
    tasks = [process_single_claim(tc) for tc in typed_claims]
    results_list = await asyncio.gather(*tasks)
```

What to say:
- `/analyze` is lighter (extract + classify).
- `/investigate` is full evidence investigation and runs multiple claim checks in parallel.

## 3) Investigation Pipeline

Source: `backend/app/services/investigation/orchestrator.py`

```python
# Phase 1 quick checks
misinfo_match = self.misinfo_checker.check(claim.text)
wiki_result = await self.wikidata_verifier.quick_fact_check(claim.text)
fact_checks = await self.google_factchecker.search(claim.text)

# Phase 2 deep strategy search
strategy_cls = StrategyFactory.get_strategy(claim.claim_type)
investigation_result = await asyncio.wait_for(strategy.execute(ctx), timeout=45.0)
```

What to say:
- Pipeline is staged: quick authoritative checks first, deep strategy search second.
- Early-stop logic is used if confidence is already decisive.

## 4) Verdict Engine Contract

Source: `backend/app/services/investigation/verdict_engine.py`

```python
# IMPORTANT: verdict is evidence-driven
if not claim.is_checkable:
    return self._create_not_checkable_result(claim)

evidence = await self.orchestrator.investigate(claim)

if evidence.override_verdict:
    ...

verdict, confidence, summary = await run_in_threadpool(
    self.synthesizer.synthesize,
    evidence,
    claim.text
)
```

What to say:
- Non-checkable claims are explicitly handled.
- Verdict decision is deterministic from evidence/synthesizer.
- LLM is used for explanation enrichment, not core evidence aggregation.

## 5) History and Extension/Web Sync

Sources:
- `backend/app/api/v3/endpoints/analyze.py`
- `backend/app/api/v1/history.py`

```python
# Saved during v3 investigate
if result.verdict.value != "not_checkable":
    db_check = Check(
        user_id=current_user["user_id"],
        claim=result.original_text,
        verdict=result.verdict.value,
        confidence=conf_label,
        explanation=result.evidence_summary,
        pipeline_version="3.0.0",
    )
    db.add(db_check)
await db.commit()
```

```python
@router.get("", response_model=HistoryListResponse)
async def get_history(...):
    query = select(Check).where(Check.user_id == user_id).order_by(Check.created_at.desc())
```

What to say:
- Extension verification saves to the same `checks` table.
- Web history and extension activity can stay in sync as long as both use same backend + same auth user.

## 6) 30-Second Review Pitch

- "v3 pipeline is input -> claim extraction -> typing -> orchestrated evidence search -> deterministic verdict -> history persistence."