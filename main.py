from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl, Field
from urllib.parse import urlparse
from datetime import datetime
from dateutil import parser

# Instantiate the FastAPI application
app = FastAPI(title="Veritas API")

def normalize_date(raw_date: str | None) -> str:
    if not raw_date:
        return "Unknown"
    try:
        parsed = parser.parse(raw_date)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return "Unknown"


# Define the inbound payload schema (what the extension sends)
class AnalyzeRequest(BaseModel):  # Defines the request model
    url: HttpUrl = Field(..., description="URL the text came from")  # Requires a valid URL
    title: str | None = Field(None, description="Optional article title")  # Allows optional title
    text: str = Field(..., min_length=1, description="Extracted visible article text")  # Requires non-empty extracted text
    published_at: str | None = Field(None, description="Raw publication date string from the page")  # Accepts raw publication date

# Response schema aligned to UI needs
class AnalyzeResponse(BaseModel):
    # Overall request status
    ok: bool

    # Article overview
    source: str | None = Field(None, description="Publisher or domain name")
    publication_date: str | None = Field(None, description="Published date if available")
    claims_detected: int = Field(..., ge=0, description="Number of claims detected")

    # Credibility signals (0.0 to 1.0 for UI bars)
    evidence_presence: float = Field(..., ge=0.0, le=1.0)
    language_certainty: float = Field(..., ge=0.0, le=1.0)
    source_reputation: float = Field(..., ge=0.0, le=1.0)

    # Verdict section
    verdict: str = Field(..., description="Pending, True, False, Mixed, Misleading")
    summary: str = Field(..., description="Short verdict explanation")


# Health check endpoint to verify server is running
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    
    # Parse the URL string
    parsed = urlparse(str(request.url))  # Convert HttpUrl to string
    domain = parsed.netloc  # Extract domain (e.g. www.nytimes.com)
    
    publication = normalize_date(request.published_at)
    
    return AnalyzeResponse(
        ok=True,
        source=domain,
        publication_date=publication,
        claims_detected=0,
        evidence_presence=0.3,
        language_certainty=0.4,
        source_reputation=0.35,
        verdict="Pending",
        summary="Enable analysis wiring later to populate this."
    )
