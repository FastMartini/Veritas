from __future__ import annotations  # Why: Postpones annotation evaluation.


# -----------------------------
# Standard Library
# -----------------------------

import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse


# -----------------------------
# Third-Party Libraries
# -----------------------------

import spacy
from dateutil import parser
from dotenv import load_dotenv
from fastapi import FastAPI
from google import genai
from pydantic import BaseModel, Field, HttpUrl


# -----------------------------
# Environment Initialization
# -----------------------------

# Why: Load .env from the same directory as main.py (project root), regardless of where uvicorn is launched from.
BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=DOTENV_PATH, override=True)

# Why: Read API key from env and fail fast if missing. This avoids google.genai auto-detection issues.
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError(f"Missing GOOGLE_API_KEY (or GEMINI_API_KEY). Expected .env at: {DOTENV_PATH}")

# Why: Create the Gemini client once at startup for stable performance and deterministic auth mode.
genai_client = genai.Client(api_key=API_KEY)


# -----------------------------
# App + NLP init
# -----------------------------

# Why: Create the API instance once.
app = FastAPI(title="Veritas API")

# Why: Load NLP resources once so each request is fast and latency is stable.
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None


# -----------------------------
# Request/Response models
# -----------------------------

class Claim(BaseModel):
    id: str = Field(..., description="Stable identifier for mapping results back to the claim")
    text: str = Field(..., description="Claim text")
    score: int = Field(..., description="Ranking score used for ordering")
    sentence_index: int = Field(..., ge=0, description="Index of the sentence in the document")


class ExtractRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL the text came from")
    title: str | None = Field(None, description="Optional article title")
    text: str = Field(..., min_length=1, description="Extracted visible article text")
    published_at: str | None = Field(None, description="Raw publication date string from the page")
    max_claims: int = Field(6, ge=1, le=12, description="Max claims to extract")


class ExtractResponse(BaseModel):
    ok: bool
    source: str | None = Field(None, description="Publisher or domain name")
    publication_date: str | None = Field(None, description="Published date if available")
    claims_detected: int = Field(..., ge=0, description="Number of claims detected")
    claims: list[Claim] = Field(default_factory=list, description="Extracted claims")


class AnalyzeRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL for context")
    source: str | None = Field(None, description="Publisher/domain")
    publication_date: str | None = Field(None, description="Normalized publication date")
    claims: list[Claim] = Field(default_factory=list, description="Claims to analyze")


class AnalyzeResponse(BaseModel):
    ok: bool
    verdict: str = Field(..., description="True, False, Mixed, Misleading, Insufficient")
    summary: str = Field(..., description="Short verdict explanation")


# -----------------------------
# Helpers for extraction
# -----------------------------

def normalize_date(raw_date: str | None) -> str:
    # Why: UI expects a stable date string; unknown must not break rendering.
    if not raw_date:
        return "Unknown"
    try:
        parsed = parser.parse(raw_date)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return "Unknown"


def normalize_text(text: str) -> str:
    # Why: Preserve newlines for line-based cleaning, but reduce whitespace noise.
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def strip_boilerplate_lines(text: str) -> str:
    # Why: Removes common non-article lines so they don’t become “claims.”
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
    # Why: Prefer sentences that are more verifiable (entities, numbers, attribution).
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


def is_claim_sentence(sent) -> bool:
    # Why: Gate out fragments, questions, and tiny sentences to keep claims high-signal.
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


def stable_claim_id(claim_text: str) -> str:
    # Why: Normalizing before hashing prevents whitespace/case from changing IDs.
    canonical = " ".join((claim_text or "").split()).strip().lower()
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:12]


def extract_claims(text: str, max_claims: int) -> list[Claim]:
    # Why: Extract and rank candidate claim sentences and return stable Claim objects.
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

def extract_first_json_object(text: str) -> str:
    # Why: Models sometimes return extra text; this extracts the first {...} block so json.loads can succeed.
    if not text:
        return ""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


# -----------------------------
# Endpoints
# -----------------------------

@app.get("/health")
def health_check():
    # Why: Simple ping to confirm server is alive.
    return {"status": "ok"}


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest):
    # Why: Derive a stable source label from the URL.
    parsed = urlparse(str(req.url))
    domain = parsed.netloc

    # Why: Normalize date and extract claims for analysis.
    publication = normalize_date(req.published_at)
    claims = extract_claims(req.text, int(req.max_claims))

    return ExtractResponse(
        ok=True,
        source=domain,
        publication_date=publication,
        claims_detected=len(claims),
        claims=claims,
    )


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    # Why: If there are no claims, don't waste a model call.
    if not req.claims:
        return AnalyzeResponse(
            ok=True,
            verdict="Insufficient",
            summary="No claims detected to analyze.",
        )

    # Why: Keep the model input bounded to the claims and metadata you extracted.
    agent_input = {
        "source": req.source or "Unknown",
        "publication_date": req.publication_date or "Unknown",
        "claims": [{"id": c.id, "text": c.text} for c in req.claims],
    }

    # Why: This is a language-based plausibility verdict (no web access, no evidence retrieval yet).
    prompt = (
        "You are evaluating ONLY the claims provided. You do NOT have web access or external evidence.\n"
        "Goal: provide a language-based plausibility verdict based on clarity, specificity, attribution, and internal consistency.\n"
        "If the claims are too vague or not checkable from general knowledge + wording, return 'Insufficient'.\n\n"
        "Return STRICT JSON only (no markdown, no extra text):\n"
        '{ "verdict": "True|False|Mixed|Misleading|Insufficient", "summary": "string" }\n\n'
        f"Source: {agent_input['source']}\n"
        f"Publication Date: {agent_input['publication_date']}\n\n"
        "Claims:\n"
        f"{json.dumps(agent_input['claims'], indent=2)}"
    )

    try:
        # Why: Single model call is the simplest MVP path to verdict + summary.
        resp = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        raw_text = (resp.text or "").strip()
        print("RAW GEMINI OUTPUT:", raw_text)

        # Why: Try strict JSON first; if it fails, attempt to extract the first JSON object.
        try:
            parsed = json.loads(raw_text)
        except Exception:
            recovered = extract_first_json_object(raw_text)
            parsed = json.loads(recovered)

        return AnalyzeResponse(
            ok=True,
            verdict=str(parsed.get("verdict", "Insufficient")),
            summary=str(parsed.get("summary", "No summary provided.")),
        )

    except Exception as e:
        # Why: The Gemini SDK raises structured errors; handle quota/rate limit cleanly for the UI.
        msg = f"{type(e).__name__}: {str(e)}"

        is_quota = "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()

        if is_quota:
            return AnalyzeResponse(
                ok=False,
                verdict="Insufficient",
                summary="Gemini quota/rate limit hit. Try again in ~15 seconds. If it keeps happening, your API key currently has 0 request/token quota for this model.",
            )

        return AnalyzeResponse(
            ok=False,
            verdict="Insufficient",
            summary=f"Agent error: {type(e).__name__}: {str(e)}",
        )