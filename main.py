from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl, Field
from urllib.parse import urlparse
from dateutil import parser
import re
import spacy


# Load NLP resources once to keep request latency stable
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None


app = FastAPI(title="Veritas API")


def normalize_date(raw_date: str | None) -> str:
    # UI expects a stable date string; unknown must not break rendering
    if not raw_date:
        return "Unknown"
    try:
        parsed = parser.parse(raw_date)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return "Unknown"


def normalize_text(text: str) -> str:
    # Preserve newlines since boilerplate filtering is line-based
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def strip_boilerplate_lines(text: str) -> str:
    # Removes known non-article tokens so they do not pollute sentence ranking
    lines = (text or "").splitlines()
    cleaned_lines: list[str] = []

    blocked_exact = {"ADVERTISEMENT", "Supported by"}

    for line in lines:
        s = line.strip()
        if not s:
            continue

        if s in blocked_exact:
            continue

        low = s.lower()
        if low.startswith("advertisement") or low.startswith("supported by"):
            continue

        cleaned_lines.append(s)

    return "\n".join(cleaned_lines).strip()


def score_sentence(sent) -> int:
    # Prefer sentences that are typically more verifiable (entities, numbers, attribution)
    score = 0

    has_subject = any(t.dep_ in ("nsubj", "nsubjpass") for t in sent)
    has_verb = any(t.pos_ == "VERB" for t in sent)

    if has_subject:
        score += 2
    if has_verb:
        score += 2

    if len(list(sent.ents)) > 0:
        score += 2

    if any(t.like_num for t in sent):
        score += 2

    reporting_verbs = {
        "say", "said", "told", "report", "reported", "claim", "claimed", "announce", "announced"
    }
    if any(t.pos_ == "VERB" and t.lemma_.lower() in reporting_verbs for t in sent):
        score += 1

    return score


def is_claim_sentence(sent) -> bool:
    # Hard gate removes fragments/questions so downstream analysis stays high-signal
    s = sent.text.strip()
    if not s:
        return False
    if s.endswith("?"):
        return False
    if len(s) < 40:
        return False

    has_subject = any(t.dep_ in ("nsubj", "nsubjpass") for t in sent)
    has_verb = any(t.pos_ == "VERB" for t in sent)
    return has_subject and has_verb


def extract_claims(text: str, max_claims: int) -> list[str]:
    # Cleanup first, then parse/rank
    cleaned = strip_boilerplate_lines(normalize_text(text))
    if not cleaned:
        return []

    if nlp is None:
        raise RuntimeError("spaCy model en_core_web_sm is not installed")

    doc = nlp(cleaned)

    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()

    for sent in doc.sents:
        if not is_claim_sentence(sent):
            continue

        claim = sent.text.strip()
        key = claim.lower()
        if key in seen:
            continue

        seen.add(key)
        candidates.append((score_sentence(sent), claim))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return [claim for _, claim in candidates[:max_claims]]


# ----- Request/Response models -----

class ExtractRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL the text came from")
    title: str | None = Field(None, description="Optional article title")
    text: str = Field(..., min_length=1, description="Extracted visible article text")
    published_at: str | None = Field(None, description="Raw publication date string from the page")
    max_claims: int = Field(12, ge=1, le=50, description="Max claims to extract")


class ExtractResponse(BaseModel):
    ok: bool
    source: str | None = Field(None, description="Publisher or domain name")
    publication_date: str | None = Field(None, description="Published date if available")
    claims_detected: int = Field(..., ge=0, description="Number of claims detected")
    claims: list[str] = Field(default_factory=list, description="Extracted claims")


# Keep /analyze reserved for the agent step; stubbed for now
class AnalyzeRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL for context")
    source: str | None = Field(None, description="Publisher/domain")
    publication_date: str | None = Field(None, description="Normalized publication date")
    claims: list[str] = Field(default_factory=list, description="Claims to analyze")


class AnalyzeResponse(BaseModel):
    ok: bool
    verdict: str = Field(..., description="Pending, True, False, Mixed, Misleading")
    summary: str = Field(..., description="Short verdict explanation")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest):
    parsed = urlparse(str(req.url))
    domain = parsed.netloc

    publication = normalize_date(req.published_at)

    cap = int(req.max_claims)
    claims = extract_claims(req.text, cap)

    return ExtractResponse(
        ok=True,
        source=domain,
        publication_date=publication,
        claims_detected=len(claims),
        claims=claims,
    )


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    # Agent integration comes next; this is a stable placeholder contract
    return AnalyzeResponse(
        ok=True,
        verdict="Pending",
        summary=f"Ready for agent. Received {len(req.claims)} claims.",
    )
