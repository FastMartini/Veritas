# schemas.py  # defines strict request/response shapes for FastAPI

from pydantic import BaseModel, Field        # BaseModel for schemas, Field for constraints/meta
from typing import List, Optional            # typing helpers for optional fields and lists

class AnalyzeRequest(BaseModel):             # request body sent by the extension
    url: Optional[str] = Field(              # optional: article URL (used for caching/provenance)
        default=None, description="Source URL of the article"
    )
    title: Optional[str] = Field(            # optional: page title (gives context to pipeline)
        default=None, description="Page title if available"
    )
    text: str = Field(                       # required: full article body to analyze
        ...,                                 # "..." means required in Pydantic
        min_length=200,                      # guard: too-short pages aren’t useful
        description="Full article body text (≥200 characters)"
    )

class EvidenceSnippet(BaseModel):            # one retrieved evidence snippet
    snippet: str = Field(                    # the evidence sentence(s) shown to the user
        ..., description="Short evidence text supporting/refuting the claim"
    )
    source: str = Field(                     # canonical link to the evidence source
        ..., description="URL of the evidence source"
    )
    retrieval_score: float = Field(          # normalized relevance [0,1] from retrieval/rerank
        ..., ge=0.0, le=1.0, description="0–1 relevance score"
    )

class ClaimResult(BaseModel):                # per-claim stance result
    claim: str = Field(                      # extracted claim text
        ..., description="Extracted claim text"
    )
    label: str = Field(                      # stance label: supported/refuted/unclear
        ..., description="supported | refuted | unclear"
    )
    confidence: float = Field(               # stance confidence [0,1] (e.g., softmax prob)
        ..., ge=0.0, le=1.0, description="Model confidence 0–1"
    )
    evidence: EvidenceSnippet = Field(       # top evidence object associated with the claim
        ..., description="Top evidence snippet and source"
    )

class AnalyzeResponse(BaseModel):            # overall article verdict
    article_label: str = Field(              # High/Medium/Low credibility band
        ..., description="High | Medium | Low credibility"
    )
    article_score: float = Field(            # numeric score [0,1] (used for your badge %)
        ..., ge=0.0, le=1.0, description="0–1 credibility score"
    )
    claims_checked: int = Field(             # number of claims processed
        ..., ge=0, description="Number of claims analyzed"
    )
    claims: List[ClaimResult] = Field(       # list of per-claim results (can be empty)
        default_factory=list, description="Per-claim results with evidence and stance"
    )
