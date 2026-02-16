# Veritas v0.2.0 – Claim Extraction Implementation

## Overview

Version 0.2.0 introduces structured claim extraction within the FastAPI backend.  
This release transitions Veritas from basic request validation into meaningful content analysis.

The goal of this version is to identify and count factual claims within an article’s visible text before external agent evaluation.

---

## Objective

Prove that:

- Article body text can be processed server-side
- Claims can be programmatically detected
- The backend can return structured claim metadata to the client

This establishes the foundation for ADK-based evidence verification in future versions.

---

## Architectural Changes

### Backend (FastAPI)

- Integrated NLP processing pipeline
- Sentence segmentation using spaCy
- Heuristic-based factual claim detection
- Structured JSON response containing:
  - `claims_detected`
  - Processed sentence count

### Data Flow

1. Extension extracts:
   - URL
   - Title
   - Visible article text
   - Raw publication date

2. Client sends payload to: POST/analyze

3. Backend:
- Normalizes text
- Splits into sentences
- Applies claim detection logic
- Returns structured JSON

4. Popup renders claim count in: Article Overview → Claims Detected


---

## Claim Detection Logic (v0.2.0)

Claims are defined as declarative, non-question sentences that contain both a grammatical subject and a verb, meet a minimum length threshold, and are ranked using entity/number/attribution signals. Each claim receives a deterministic SHA-256-derived ID to keep mapping stable across runs.

Current implementation uses rule-based heuristics:

**Sentences containing:**
  - Quantifiable information
  - Dates
  - Named entities
  - Declarative factual structure

**Excludes:**
  - Questions
  - Pure opinion statements
  - Short fragments

This is intentionally lightweight and deterministic to validate backend behavior before integrating an external verification agent.

### 1. Text Normalization

Ensures stable sentence parsing and hashing behavior across inconsistent HTML sources.

```python
    def normalize_text(text: str) -> str:
        s = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        s = re.sub(r"[ \t]+", " ", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        return s.strip()
```

### 2. Boilerplate Removal (Soft Filter)

Removes common non-article tokens that would otherwise pollute claim ranking.

```python

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

```

### 3. Claim Gate (Hard Filter)

Filters out fragments, short text, and questions before ranking.

```python

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

```

### 4. Sentence Ranking Logic

Ranks sentences based on verifiability indicators.

Signals include:  
  - Subject presence

  - Verb presence

  - Named entities

  - Numeric references

  - Reporting verbs

```python
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

    reporting_verbs = {
        "say", "said", "told", "report", "reported",
        "claim", "claimed", "announce", "announced"
    }

    if any(t.pos_ == "VERB" and t.lemma_.lower() in reporting_verbs for t in sent):
        score += 1

    return score

```

### 5. Stable Claim ID Generation

Generates deterministic identifiers to maintain mapping consistency between extraction and future agent analysis.

```python
def stable_claim_id(claim_text: str) -> str:
    canonical = " ".join((claim_text or "").split()).strip().lower()
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:12]

```

### 6. Claim Extraction Pipeline:

Combines normalization, filtering, scoring, deduplication, ranking, and structured object return.

```python

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
```

### 7. Frontend Rendering of Ranked Claims

Ensures claims are displayed in ranked order with stable IDs

```python

if (claimsList) {
  claimsList.innerHTML = "";
  const claims = Array.isArray(data.claims) ? data.claims : [];

  for (const c of claims) {
    const li = document.createElement("li");
    const id = c?.id ? `[${c.id}] ` : "";
    li.textContent = `${id}${c?.text ?? ""}`.trim();
    claimsList.appendChild(li);
  }
}

```

  

---
## Results

### Example Article Webpage:


<img width="1512" height="829" alt="Screenshot 2026-02-16 at 5 28 12 PM" src="https://github.com/user-attachments/assets/c20e4e0f-393b-4a21-97b7-8e38fa198752" />
https://www.nytimes.com/2026/02/11/us/trump-administration-el-paso-airspace-closure-questions.html


### Example Request Schema:

```json
{
  "url": "https://example.com/",
  "title": "string",
  "text": "string",
  "published_at": "string",
  "max_claims": 12
}
```

### Example Response Schema:

```json

{
  "ok": true,
  "source": "string",
  "publication_date": "string",
  "claims_detected": 0,
  "claims": [
    {
      "id": "string",
      "text": "string",
      "score": 0,
      "sentence_index": 0
    }
  ]
}

```

### Response Schema (via Console) from Example Article Webpage (nytimes.com)
<img width="3024" height="1312" alt="image" src="https://github.com/user-attachments/assets/94f2f1b3-b3ae-4f2d-842c-e9632c33662d" />


### Popup Rendering:

<img width="362" height="605" alt="Screenshot 2026-02-16 at 5 49 01 PM" src="https://github.com/user-attachments/assets/9e51f017-4671-4029-8a17-fcb16529d084" />


<img width="335" height="210" alt="Screenshot 2026-02-16 at 5 50 22 PM" src="https://github.com/user-attachments/assets/12322e73-0065-4c93-bebe-77f11a70b0e2" />

*scrolling features to view all claims within the Extracted Claims dropdown*


