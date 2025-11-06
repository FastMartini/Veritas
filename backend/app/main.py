# backend/app/main.py)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .pipeline.claims import extract_claims
from .schemas import AnalyzeRequest, AnalyzeResponse, ClaimResult, EvidenceSnippet
from .config import AGGREGATION
from .pipeline.retrieve import fetch_snippets_for_claim
from .pipeline.rerank import rerank


# every import should be at top-level with comments
from .pipeline.nli import stance  # import a stubbed stance for now

@app.post("/analyze", response_model=AnalyzeResponse)  # declare POST route with response model
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:   # annotate return type for clarity
    claims = extract_claims(req.text)                  # 1) extract candidate claims
    results: list[ClaimResult] = []                    # container for per-claim outputs

    for c in claims:                                   # iterate each claim
        snips = fetch_snippets_for_claim(c)            # 2) retrieve candidate snippets
        top = rerank(c, snips)                         # 3) rerank to keep best few

        if top:                                        # if we have any evidence
            lbl, conf = stance(c, top[0].snippet)      # 4) run stance on best snippet
            results.append(ClaimResult(                # pack a positive result
                claim=c,
                label=lbl,
                confidence=conf,
                evidence=top[0],
            ))
        else:                                          # no evidence found for this claim
            results.append(ClaimResult(                # emit an 'unclear' result
                claim=c,
                label="unclear",
                confidence=0.0,
                evidence=EvidenceSnippet(
                    snippet="(no evidence found)",
                    source="about:blank",
                    retrieval_score=0.0,
                ),
            ))

    # 5) aggregate to article score/label
    score = min(1.0, len(results) / 10.0)              # crude fraction mapped to [0,1]
    if score >= AGGREGATION["high_min"]:               # thresholding to bands
        label = "High"
    elif score >= AGGREGATION["med_min"]:
        label = "Medium"
    else:
        label = "Low"

    return AnalyzeResponse(                            # return typed response
        article_label=label,
        article_score=score,
        claims_checked=len(results),
        claims=results,
    )
