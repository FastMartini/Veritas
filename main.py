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

def normalize_text(text: str) -> str:  # Comment: normalizes spacing while preserving newlines for line-based filters
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n")  # Comment: normalizes line endings
    s = re.sub(r"[ \t]+", " ", s)  # Comment: collapses spaces/tabs but keeps newlines
    s = re.sub(r"\n{3,}", "\n\n", s)  # Comment: prevents massive vertical gaps
    return s.strip()  # Comment: trims ends

def strip_boilerplate_lines(text: str) -> str:  # Comment: removes common non-article lines that pollute extraction
    lines = (text or "").splitlines()  # Comment: splits text into individual lines
    cleaned_lines = []  # Comment: stores lines that survive filtering
    blocked_exact = {  # Comment: exact lines to remove when they appear alone
        "ADVERTISEMENT",  # Comment: removes ad marker
        "Supported by",  # Comment: removes sponsor marker
    }  # Comment: ends blocked set
    for line in lines:  # Comment: iterates each line
        s = line.strip()  # Comment: trims whitespace from the line
        if not s:  # Comment: skips empty lines
            continue  # Comment: moves to next line
        if s in blocked_exact:  # Comment: skips known boilerplate tokens
            continue  # Comment: moves to next line
        if s.lower().startswith("advertisement"):  # Comment: catches variants like "Advertisement"
            continue  # Comment: moves to next line
        if s.lower().startswith("supported by"):  # Comment: catches variants like "Supported by ..."
            continue  # Comment: moves to next line
        cleaned_lines.append(s)  # Comment: keeps line
    return "\n".join(cleaned_lines).strip()  # Comment: rejoins cleaned lines and returns

def score_sentence(sent) -> int:  # Comment: assigns a simple quality score to a sentence
    score = 0  # Comment: initializes score
    has_subject = False  # Comment: tracks if sentence has a subject
    has_verb = False  # Comment: tracks if sentence has a verb
    for token in sent:  # Comment: iterates tokens in the sentence
        if token.dep_ in ("nsubj", "nsubjpass"):  # Comment: checks subject dependency
            has_subject = True  # Comment: marks subject found
        if token.pos_ == "VERB":  # Comment: checks verb part of speech
            has_verb = True  # Comment: marks verb found
    if has_subject:  # Comment: boosts if subject exists
        score += 2  # Comment: adds points
    if has_verb:  # Comment: boosts if verb exists
        score += 2  # Comment: adds points

    has_entity = len(list(sent.ents)) > 0  # Comment: checks for named entities
    if has_entity:  # Comment: boosts entity presence
        score += 2  # Comment: adds points

    has_number = any(t.like_num for t in sent)  # Comment: checks if sentence contains a number
    if has_number:  # Comment: boosts number presence
        score += 2  # Comment: adds points

    reporting_verbs = {"say", "said", "told", "report", "reported", "claim", "claimed", "announce", "announced"}  # Comment: common reporting verbs
    has_reporting_verb = any(t.lemma_.lower() in reporting_verbs for t in sent if t.pos_ == "VERB")  # Comment: checks for reporting verb
    if has_reporting_verb:  # Comment: boosts reporting verb presence
        score += 1  # Comment: adds points

    return score  # Comment: returns total score

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

def extract_claims(text: str, max_claims: int) -> list[str]:  # Comment: extracts top max_claims ranked claim sentences
    cleaned = normalize_text(text)  # Comment: normalizes whitespace before line filtering
    cleaned = strip_boilerplate_lines(cleaned)  # Comment: removes boilerplate lines before NLP runs
    if not cleaned:  # Comment: handles empty text after cleanup
        return []  # Comment: returns no claims

    if nlp is None:  # Comment: ensures model is loaded before extraction
        raise RuntimeError("spaCy model en_core_web_sm is not installed")  # Comment: fails loudly for debugging

    doc = nlp(cleaned)  # Comment: runs spaCy parsing and sentence segmentation

    candidates = []  # Comment: stores (score, claim) pairs
    seen = set()  # Comment: dedupes claims

    for sent in doc.sents:  # Comment: iterates sentences
        if is_claim_sentence(sent):  # Comment: applies base claim filter
            claim = sent.text.strip()  # Comment: extracts claim text
            key = claim.lower()  # Comment: normalizes for dedupe
            if key not in seen:  # Comment: keeps unique claims only
                seen.add(key)  # Comment: marks claim as seen
                score = score_sentence(sent)  # Comment: scores claim quality
                candidates.append((score, claim))  # Comment: stores candidate

    candidates.sort(key=lambda x: x[0], reverse=True)  # Comment: sorts by descending score
    claims = [claim for _, claim in candidates[:max_claims]]  # Comment: selects top N claims
    return claims  # Comment: returns ranked claims



# Define the inbound payload schema (what the extension sends)
class AnalyzeRequest(BaseModel):  # Defines the request model
    url: HttpUrl = Field(..., description="URL the text came from")  # Requires a valid URL
    title: str | None = Field(None, description="Optional article title")  # Allows optional title
    text: str = Field(..., min_length=1, description="Extracted visible article text")  # Requires non-empty extracted text
    published_at: str | None = Field(None, description="Raw publication date string from the page")  # Accepts raw publication date
    max_claims: int = Field(12, ge=1, le=50, description="Max claims to extract")  # Comment: caps claims returned


# Response schema aligned to UI needs
class AnalyzeResponse(BaseModel):
    # Overall request status
    ok: bool

    # Article overview
    source: str | None = Field(None, description="Publisher or domain name")
    publication_date: str | None = Field(None, description="Published date if available")
    claims_detected: int = Field(..., ge=0, description="Number of claims detected")

    claims: list[str] = Field(default_factory=list, description="Extracted claims")  # Comment: returns extracted claims for UI/debug

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
        claims=claims,
        verdict="Pending",
        summary="Pending..."
    )
