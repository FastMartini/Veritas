from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl, Field
from urllib.parse import urlparse
from dateutil import parser
import re  # Comment: used for light text normalization
import spacy  # Comment: used for sentence splitting and grammar parsing


try:  # Comment: attempts to load spaCy model
    nlp = spacy.load("en_core_web_sm")  # Comment: loads model once at startup
except Exception:  # Comment: handles missing model or load failures
    nlp = None  # Comment: sets nlp to None so the API can fail gracefully


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

def normalize_text(text: str) -> str:  # Comment: normalizes whitespace for stable NLP parsing
    cleaned = re.sub(r"\s+", " ", (text or "")).strip()  # Comment: collapses whitespace and trims ends
    return cleaned  # Comment: returns cleaned text

def is_claim_sentence(sent) -> bool:  # Comment: checks if a sentence is a claim candidate
    s = sent.text.strip()  # Comment: gets sentence text
    if not s:  # Comment: rejects empty
        return False  # Comment: not a claim
    if s.endswith("?"):  # Comment: rejects questions
        return False  # Comment: not a claim
    if len(s) < 40:  # Comment: rejects short fragments
        return False  # Comment: not a claim

    has_subject = False  # Comment: tracks subject existence
    has_verb = False  # Comment: tracks verb existence

    for token in sent:  # Comment: iterates tokens in the sentence
        if token.dep_ in ("nsubj", "nsubjpass"):  # Comment: checks for grammatical subject
            has_subject = True  # Comment: marks subject found
        if token.pos_ == "VERB":  # Comment: checks for verb POS
            has_verb = True  # Comment: marks verb found

    return has_subject and has_verb  # Comment: requires both subject and verb

def extract_claims(text: str, max_claims: int) -> list[str]:  # Comment: extracts up to max_claims claim sentences
    cleaned = normalize_text(text)  # Comment: normalizes input text
    if not cleaned:  # Comment: handles empty text
        return []  # Comment: returns no claims
    
    if nlp is None:  # Comment: ensures model is loaded before extraction
        raise RuntimeError("spaCy model en_core_web_sm is not installed")  # Comment: fails loudly for debugging

    doc = nlp(cleaned)  # Comment: runs spaCy parsing and sentence segmentation
    claims = []  # Comment: stores accepted claims
    seen = set()  # Comment: dedupes claims

    for sent in doc.sents:  # Comment: iterates sentences
        if is_claim_sentence(sent):  # Comment: applies claim filter
            claim = sent.text.strip()  # Comment: gets claim string
            key = claim.lower()  # Comment: normalizes for dedupe
            if key not in seen:  # Comment: keeps only unique claims
                seen.add(key)  # Comment: marks as seen
                claims.append(claim)  # Comment: appends claim to output
        if len(claims) >= max_claims:  # Comment: respects cap
            break  # Comment: stops once enough claims found

    return claims  # Comment: returns extracted claims



# Define the inbound payload schema (what the extension sends)
class AnalyzeRequest(BaseModel):  # Defines the request model
    url: HttpUrl = Field(..., description="URL the text came from")  # Requires a valid URL
    title: str | None = Field(None, description="Optional article title")  # Allows optional title
    text: str = Field(..., min_length=1, description="Extracted visible article text")  # Requires non-empty extracted text
    published_at: str | None = Field(None, description="Raw publication date string from the page")  # Accepts raw publication date
    max_claims: int = Field(50, ge=1, le=25, description="Max claims to extract")  # Comment: caps claims returned


# Response schema aligned to UI needs
class AnalyzeResponse(BaseModel):
    # Overall request status
    ok: bool

    # Article overview
    source: str | None = Field(None, description="Publisher or domain name")
    publication_date: str | None = Field(None, description="Published date if available")
    claims_detected: int = Field(..., ge=0, description="Number of claims detected")

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
    
    cap = int(request.max_claims)  # Comment: reads max claims cap from request
    claims = extract_claims(request.text, cap)  # Comment: extracts claims from client text

    
    return AnalyzeResponse(
        ok=True,
        source=domain,
        publication_date=publication,
        claims_detected=len(claims),
        verdict="Pending",
        summary=f"Extracted {len(claims)} claims. First 3: " + " | ".join(claims[:3])
    )
