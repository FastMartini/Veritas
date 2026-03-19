from __future__ import annotations  # Why: Postpones annotation evaluation.


# -----------------------------
# Standard Library
# -----------------------------

# Why: hashlib creates stable IDs for extracted claims.
import hashlib

# Why: json is used to serialize model input and parse Gemini output.
import json

# Why: os is used to read environment variables for API keys.
import os

# Why: re is used for text cleanup and normalization.
import re

# Why: Path helps locate the .env file reliably from the project root.
from pathlib import Path

# Why: urlparse extracts the publisher/domain from the article URL.
from urllib.parse import urlparse


# -----------------------------
# Third-Party Libraries
# -----------------------------

# Why: spaCy is used for sentence segmentation and lightweight claim extraction.
import spacy

# Why: dateutil parser normalizes many date formats into one stable format.
from dateutil import parser

# Why: dotenv loads API keys from the local .env file.
from dotenv import load_dotenv

# Why: FastAPI exposes the extract and analyze endpoints.
from fastapi import FastAPI

# Why: google.genai is the Gemini SDK used for model calls.
from google import genai

# Why: Pydantic models validate request and response payloads.
from pydantic import BaseModel, Field, HttpUrl


# -----------------------------
# Environment Initialization
# -----------------------------

# Why: Load .env from the same directory as main.py regardless of where uvicorn is launched from.
BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=DOTENV_PATH, override=True)

# Why: Read API key from env and fail fast if missing so auth issues are obvious immediately.
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError(f"Missing GOOGLE_API_KEY (or GEMINI_API_KEY). Expected .env at: {DOTENV_PATH}")

# Why: Create the Gemini client once at startup for stable performance and deterministic auth mode.
genai_client = genai.Client(api_key=API_KEY)


# -----------------------------
# App + NLP init
# -----------------------------

# Why: Create the API instance once for the lifetime of the process.
app = FastAPI(title="Veritas API")

# Why: Load NLP resources once so each request stays fast and latency remains stable.
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None


# -----------------------------
# Request/Response models
# -----------------------------

# Why: Claim objects preserve stable IDs and ranking metadata for later analysis.
class Claim(BaseModel):
    id: str = Field(..., description="Stable identifier for mapping results back to the claim")
    text: str = Field(..., description="Claim text")
    score: int = Field(..., description="Ranking score used for ordering")
    sentence_index: int = Field(..., ge=0, description="Index of the sentence in the document")


# Why: ExtractRequest carries the article content the extension pulled from the page.
class ExtractRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL the text came from")
    title: str | None = Field(None, description="Optional article title")
    text: str = Field(..., min_length=1, description="Extracted visible article text")
    published_at: str | None = Field(None, description="Raw publication date string from the page")
    max_claims: int = Field(6, ge=1, le=12, description="Max claims to extract")


# Why: ExtractResponse returns source/date metadata plus ranked claim candidates.
class ExtractResponse(BaseModel):
    ok: bool
    source: str | None = Field(None, description="Publisher or domain name")
    publication_date: str | None = Field(None, description="Published date if available")
    claims_detected: int = Field(..., ge=0, description="Number of claims detected")
    claims: list[Claim] = Field(default_factory=list, description="Extracted claims")


# Why: AnalyzeRequest now includes title and article text because political framing is often visible
# in the headline and broader article wording, not only in isolated claims.
class AnalyzeRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL for context")
    source: str | None = Field(None, description="Publisher/domain")
    publication_date: str | None = Field(None, description="Normalized publication date")
    title: str | None = Field(None, description="Article title for framing analysis")
    article_text: str | None = Field(None, description="Article text used for language and framing analysis")
    claims: list[Claim] = Field(default_factory=list, description="Claims to analyze")


# Why: AnalyzeResponse now represents estimated political leaning instead of truthfulness.
class AnalyzeResponse(BaseModel):
    ok: bool
    verdict: str = Field(..., description="Left-leaning, Center-left, Center, Center-right, Right-leaning, or Unclear")
    summary: str = Field(..., description="Short explanation of the leaning estimate")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Model confidence from 0.0 to 1.0")
    source_bias: float = Field(0.0, ge=-1.0, le=1.0, description="Estimated source bias from -1.0 left to 1.0 right")
    language_bias: float = Field(0.0, ge=-1.0, le=1.0, description="Estimated wording bias from -1.0 left to 1.0 right")
    framing_bias: float = Field(0.0, ge=-1.0, le=1.0, description="Estimated framing bias from -1.0 left to 1.0 right")


# -----------------------------
# Helpers for extraction
# -----------------------------

# Why: The UI expects a stable date string and unknown dates should not break rendering.
def normalize_date(raw_date: str | None) -> str:
    if not raw_date:
        return "Unknown"
    try:
        parsed = parser.parse(raw_date)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return "Unknown"


# Why: Preserve newlines for line-based cleaning while reducing whitespace noise.
def normalize_text(text: str) -> str:
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


# Why: Removes common non-article lines so they do not become extracted claims.
def strip_boilerplate_lines(text: str) -> str:
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


# Why: Prefer sentences that look more verifiable and information-dense.
def score_sentence(sent) -> int:
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

    reporting_verbs = {"say", "said", "told", "report", "reported", "claim", "claimed", "announce", "announced"}
    if any(t.pos_ == "VERB" and t.lemma_.lower() in reporting_verbs for t in sent):
        score += 1

    return score


# Why: Filter out fragments, questions, and tiny sentences so extracted claims stay high-signal.
def is_claim_sentence(sent) -> bool:
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


# Why: Normalizing before hashing prevents whitespace or casing from changing claim IDs.
def stable_claim_id(claim_text: str) -> str:
    canonical = " ".join((claim_text or "").split()).strip().lower()
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:12]


# Why: Extract and rank candidate claim sentences and return stable Claim objects.
def extract_claims(text: str, max_claims: int) -> list[Claim]:
    cleaned = strip_boilerplate_lines(normalize_text(text))
    if not cleaned:
        return []

    if nlp is None:
        raise RuntimeError("spaCy model en_core_web_sm is not installed")

    doc = nlp(cleaned)

    candidates: list[tuple[int, int, str]] = []
    seen: set[str] = set()

    for i, sent in enumerate(doc.sents):
        if not is_claim_sentence(sent):
            continue

        claim_text = sent.text.strip()
        key = claim_text.lower()
        if key in seen:
            continue

        seen.add(key)
        candidates.append((score_sentence(sent), i, claim_text))

    candidates.sort(key=lambda x: x[0], reverse=True)
    top = candidates[:max_claims]

    return [
        Claim(
            id=stable_claim_id(claim_text),
            text=claim_text,
            score=score,
            sentence_index=idx,
        )
        for score, idx, claim_text in top
    ]


# -----------------------------
# Helpers for analysis (Gemini)
# -----------------------------

# Why: Models sometimes return extra wrapper text, so this recovers the first JSON object.
def extract_first_json_object(text: str) -> str:
    if not text:
        return ""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


# Why: Bound article text to keep prompt size under control and avoid wasting tokens.
def bound_article_text(text: str | None, max_chars: int = 3000) -> str:
    return (text or "").strip()[:max_chars]


# Why: Clamp floats from model output so bad values do not break validation or UI assumptions.
def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


# -----------------------------
# Endpoints
# -----------------------------

# Why: Simple ping endpoint to confirm the API process is alive.
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Why: /extract derives source/date metadata and ranks claim candidates from article text.
@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest):
    parsed = urlparse(str(req.url))
    domain = parsed.netloc

    publication = normalize_date(req.published_at)
    claims = extract_claims(req.text, int(req.max_claims))

    return ExtractResponse(
        ok=True,
        source=domain,
        publication_date=publication,
        claims_detected=len(claims),
        claims=claims,
    )


# Why: /analyze now estimates political framing and leaning rather than truthfulness.
@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    # Why: Even without claims, title and article text may still contain framing signals.
    has_claims = bool(req.claims)
    has_text = bool((req.article_text or "").strip())
    has_title = bool((req.title or "").strip())

    if not has_claims and not has_text and not has_title:
        return AnalyzeResponse(
            ok=True,
            verdict="Unclear",
            summary="Not enough article content was available to estimate political leaning.",
            confidence=0.0,
            source_bias=0.0,
            language_bias=0.0,
            framing_bias=0.0,
        )

    # Why: Keep model input bounded while still giving it the strongest bias signals available.
    agent_input = {
        "source": req.source or "Unknown",
        "publication_date": req.publication_date or "Unknown",
        "title": (req.title or "").strip(),
        "article_text": bound_article_text(req.article_text, max_chars=3000),
        "claims": [{"id": c.id, "text": c.text} for c in req.claims],
    }

    # Why: The prompt explicitly bans truth-checking and asks only for political leaning estimation.
    prompt = (
        "You are analyzing ONLY the article information provided to estimate political framing and editorial leaning.\n"
        "You do NOT have web access and you must NOT fact-check truthfulness.\n\n"
        "Classify the article as one of the following:\n"
        "- Left-leaning\n"
        "- Center-left\n"
        "- Center\n"
        "- Center-right\n"
        "- Right-leaning\n"
        "- Unclear\n\n"
        "Use these signals:\n"
        "1. source_bias: Does the source/domain itself suggest a political orientation?\n"
        "2. language_bias: Does the wording use emotionally loaded or ideologically slanted language?\n"
        "3. framing_bias: Does the article emphasize one side's assumptions, concerns, or narratives over another?\n\n"
        "Scoring rules:\n"
        "- source_bias, language_bias, framing_bias must each be a float from -1.0 to 1.0\n"
        "- negative values indicate leftward leaning\n"
        "- positive values indicate rightward leaning\n"
        "- 0 means neutral, balanced, or unclear\n"
        "- confidence must be a float from 0.0 to 1.0\n\n"
        "Use 'Unclear' if the text is too short, too vague, non-political, or lacks enough framing signals.\n\n"
        "Return STRICT JSON only with no markdown and no extra text.\n"
        '{'
        '"verdict": "Left-leaning|Center-left|Center|Center-right|Right-leaning|Unclear", '
        '"summary": "string", '
        '"confidence": 0.0, '
        '"source_bias": 0.0, '
        '"language_bias": 0.0, '
        '"framing_bias": 0.0'
        '}\n\n'
        f"Source: {agent_input['source']}\n"
        f"Publication Date: {agent_input['publication_date']}\n"
        f"Title: {agent_input['title']}\n\n"
        "Claims:\n"
        f"{json.dumps(agent_input['claims'], indent=2)}\n\n"
        "Article Text Excerpt:\n"
        f"{agent_input['article_text']}"
    )

    try:
        # Why: One model call keeps the MVP simple while still returning structured leaning output.
        resp = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        # Why: Gemini may return wrapper text around JSON, so normalize before parsing.
        raw_text = (resp.text or "").strip()
        print("RAW GEMINI OUTPUT:", raw_text)

        # Why: Parse strict JSON first, then recover the first JSON object if needed.
        try:
            parsed = json.loads(raw_text)
        except Exception:
            recovered = extract_first_json_object(raw_text)
            parsed = json.loads(recovered)

        # Why: Pull numeric values safely and clamp them into the expected range.
        confidence = clamp(float(parsed.get("confidence", 0.0)), 0.0, 1.0)
        source_bias = clamp(float(parsed.get("source_bias", 0.0)), -1.0, 1.0)
        language_bias = clamp(float(parsed.get("language_bias", 0.0)), -1.0, 1.0)
        framing_bias = clamp(float(parsed.get("framing_bias", 0.0)), -1.0, 1.0)

        return AnalyzeResponse(
            ok=True,
            verdict=str(parsed.get("verdict", "Unclear")),
            summary=str(parsed.get("summary", "No summary provided.")),
            confidence=confidence,
            source_bias=source_bias,
            language_bias=language_bias,
            framing_bias=framing_bias,
        )

    except Exception as e:
        # Why: Gemini quota and rate-limit issues should surface cleanly for the popup UI.
        msg = f"{type(e).__name__}: {str(e)}"
        is_quota = "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()

        if is_quota:
            return AnalyzeResponse(
                ok=False,
                verdict="Unclear",
                summary="Gemini quota or rate limit hit. Try again shortly.",
                confidence=0.0,
                source_bias=0.0,
                language_bias=0.0,
                framing_bias=0.0,
            )

        return AnalyzeResponse(
            ok=False,
            verdict="Unclear",
            summary=f"Agent error: {type(e).__name__}: {str(e)}",
            confidence=0.0,
            source_bias=0.0,
            language_bias=0.0,
            framing_bias=0.0,
        )