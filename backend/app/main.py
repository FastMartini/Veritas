# backend/app/main.py)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .pipeline.claims import extract_claims
from .schemas import AnalyzeRequest, AnalyzeResponse, ClaimResult, EvidenceSnippet
from .config import AGGREGATION
from .pipeline.retrieve import fetch_snippets_for_claim
from .pipeline.rerank import rerank



app = FastAPI(title="Veritas API", version="0.1")

# CORS so the Chrome extension (any origin during dev) can call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "mode": "retrieval-only"}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    # 1) Extract claims from the article text
    claims = extract_claims(req.text)

    # 2) For now, stub “stance/evidence” (you can hook up retrieve/rerank/NLI later)
    results = []
    for c in claims:
        # 1) retrieve candidate evidence
        snips = fetch_snippets_for_claim(c)

        # 2) rerank candidates for the best snippet(s)
        top = rerank(c, snips)

        # 3) run stance/NLI on the best snippet (if any)
        if top:
            lbl, conf = stance(c, top[0].snippet)
            results.append(ClaimResult(
                claim=c,
                label=lbl,
                confidence=conf,
                evidence=top[0],
        ))
    else:
        results.append(ClaimResult(
            claim=c,
            label="unclear",
            confidence=0.0,
            evidence=EvidenceSnippet(
                snippet="(no evidence found)",
                source="about:blank",
                retrieval_score=0.0,
            ),
        ))


    # 3) Make a simple article score = fraction of allowed claims we found
    #    and map to High/Medium/Low using AGGREGATION thresholds.
    max_score = 1.0
    score = min(max_score, len(results) / 10.0)
    if score >= AGGREGATION["high_min"]:
        label = "High"
    elif score >= AGGREGATION["med_min"]:
        label = "Medium"
    else:
        label = "Low"

    return AnalyzeResponse(
        article_label=label,
        article_score=score,
        claims_checked=len(results),
        claims=results,
    )
