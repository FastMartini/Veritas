# Claim Extraction Pipeline

**Case ID:** VER-PIPELINE-001

**User Story** -
As a Veritas user,
I want the backend pipeline to identify and rank factual claims from an article,
so that the rest of the fact-checking system can retrieve evidence and assess each claim’s credibility.
<img width="2683" height="3840" alt="Claim_Extraction_UC" src="https://github.com/user-attachments/assets/698c6bb0-2d15-43cb-a6de-8a1cae357afe" />

# Goal
Identify and rank factual statements (“claims”) inside an article so they can be verified against trusted sources in later stages of the pipeline (evidence retrieval → re-ranking → NLI/stance detection).

# Implementation Details
This section explains how claims.py, schemas.py, and config.py work together to extract claims from article text and shape the API contract.

**Module Roles (at a glance)**

* **claims.py** – Runs spaCy to split the article into sentences, filters factual-sounding ones, scores them, deduplicates, and returns the top-N claims.

* **schemas.py** – Defines the API types (request/response) for the /analyze endpoint using Pydantic.

* **config.py** – Central configuration: trusted domains, extraction knobs (limits/thresholds), aggregation cutoffs, and other pipeline settings.

# claims.py - How Claims Are Extracted

1. Load spaCy once (en_core_web_sm) to enable sentence segmentation and named entity recognition (NER).
<img width="860" height="54" alt="Screenshot 2025-09-24 at 1 56 24 AM" src="https://github.com/user-attachments/assets/1de666f3-d658-4662-b307-989d4c3f9bdd" />

2. Clean the input text (collapse whitespace).
<img width="785" height="65" alt="Screenshot 2025-09-24 at 1 56 51 AM" src="https://github.com/user-attachments/assets/b6a028c3-8185-4700-aaad-62c3b519aed0" />

3. Segment to sentences, then apply filters:

* Token length within bounds (default 8–40).

* Must contain a named entity (PERSON/ORG/GPE/etc.) or a numeric fact (digits or %) if configured.

* Declarative (skip questions like ...?).
<img width="867" height="294" alt="Screenshot 2025-09-24 at 1 57 39 AM" src="https://github.com/user-attachments/assets/8cd630e7-7a78-4710-8543-30f4ae9221b6" />

4. Score each candidate with a salience function:

* +0.4 if length is in the sweet spot.

* +0.35 if it contains a named entity.

* +0.15 if it contains a number/percent.

* +0.1 if the sentence appears early in the article.
<img width="690" height="536" alt="Screenshot 2025-09-24 at 2 05 17 AM" src="https://github.com/user-attachments/assets/da83f3f9-3e45-4f8f-9344-ee472d57709f" />


5. Deduplicate near-identical sentences.
<img width="562" height="153" alt="Screenshot 2025-09-24 at 2 05 54 AM" src="https://github.com/user-attachments/assets/f87cd64c-55e5-4a0c-a7e6-d83b241fa146" />

6. Return the top-N (default 12) claim strings.
<img width="263" height="33" alt="Screenshot 2025-09-24 at 2 06 11 AM" src="https://github.com/user-attachments/assets/26528c94-c537-4578-b5dd-0af98c807485" />

**Key Functions**
* _clean(text): normalizes whitespace.

* _token_len(s): rough token count via whitespace split.

* _has_named_entity(sent): true if NER finds PERSON/ORG/GPE/LOC/DATE/TIME/MONEY/PERCENT.

* _has_numeric_fact(s): true if any digit or % is present.

* _is_declarative(s): rejects questions; lightly prefers factual cue words.

* _salience(sent, idx): computes a 0–1 score from length, entities, numbers, and early position.

* extract_claims(text, max_claims=None): orchestrates the pipeline and returns a List[str].

# schemas.py — API Contract (Pydantic)
**Request: AnalyzeRequest**

* **url** (optional): article URL (for caching/provenance).

* **title** (optional): page title.

* **text** (required, min_length=200): full article body to analyze.

  * Why 200? Guards against homepages/short blurbs that won’t yield meaningful claims.
<img width="697" height="224" alt="Screenshot 2025-09-24 at 2 18 48 AM" src="https://github.com/user-attachments/assets/004ebd47-d809-441b-a585-b72595138f51" />

**Response: AnalyzeResponse**
* **article_label** (string): **"High" | "Medium" | "Low"** credibility (set later by aggregation).

* **article_score** (float, 0–1): numeric credibility score (used for the badge/UX).

* **claims_checked** (int): how many claims were processed.

* **claims** (list of **ClaimResult**): per-claim outputs for the UI.
<img width="638" height="223" alt="Screenshot 2025-09-24 at 2 19 50 AM" src="https://github.com/user-attachments/assets/a039f4cb-c525-4b56-9c1b-e1c4f204ad89" />

**Per-claim objects**

* **ClaimResult**:

  * **claim**: the extracted claim text.

  * **label**: "supported" | "refuted" | "unclear" (set later by stance/NLI).

  * **confidence**: 0–1 confidence for the stance.

  * **evidence**: an EvidenceSnippet.
<img width="651" height="231" alt="Screenshot 2025-09-24 at 2 20 47 AM" src="https://github.com/user-attachments/assets/0d03ee43-c395-4a0e-abd3-bf3258de4c4b" />

* **EvidenceSnippet**:
  * **snippet**: evidence text shown to the user.

  * **source**: URL of the evidence.

  * **retrieval_score**: normalized relevance (0–1) from retrieval/rerank.
<img width="675" height="187" alt="Screenshot 2025-09-24 at 2 21 21 AM" src="https://github.com/user-attachments/assets/63ba6847-d8b9-4903-98dd-da7d5a3aee9a" />

Why Pydantic? Strong validation and consistent JSON shape for the extension and tests.

# config.py — Central Configuration
* **TRUSTED_SITES:**
  *   allowlist of domains for evidence retrieval (news, fact-checking, science, gov, data).
  *   Used by retrieval/rerank stages (later steps), not by extraction itself.
<img width="808" height="357" alt="Screenshot 2025-09-24 at 2 28 14 AM" src="https://github.com/user-attachments/assets/5e0c8537-ea3b-4e4d-aca8-f810104ca2ed" />

* **CLAIM_EXTRACTION:**

  * **max_claims**: cap of returned claims per article (default 12).

  * **min_tokens / max_tokens**: sentence length bounds.

  * **require_entity_or_digit**: gate to reduce generic sentences.
<img width="647" height="155" alt="Screenshot 2025-09-24 at 2 27 39 AM" src="https://github.com/user-attachments/assets/58d8216b-70df-44bc-a606-848d5f27c548" />

* **AGGREGATION:**

  * Maps final article score to label bands: high_min (≥0.75 ⇒ High), med_min (≥0.55 ⇒ Medium), else Low.
<img width="516" height="125" alt="Screenshot 2025-09-24 at 2 27 26 AM" src="https://github.com/user-attachments/assets/e9d0ff3e-f4e8-4895-b8b9-c364dacbca78" />

* **RETRIEVAL, RERANK, NLI, CACHE:**

  * Knobs for later pipeline stages (doc counts, snippet counts, timeouts, embedding usage, stance model name, confidence cutoffs, simple caching limits).

<img width="642" height="368" alt="Screenshot 2025-09-24 at 2 27 15 AM" src="https://github.com/user-attachments/assets/4bf7948c-81c9-4f5d-8b03-1bf4d5d34571" />

# Proof of Concept

**Smoke Test using _claim_test.py**:
<img width="1055" height="352" alt="_Claim_test" src="https://github.com/user-attachments/assets/307fbfe1-de04-4b5f-9589-47231b43e664" />

**Result**:

<img width="660" height="62" alt="_Claim_test_result" src="https://github.com/user-attachments/assets/5ee3f53c-554c-45c1-917c-a79440c5ba34" />

# Data Flow (how these files interact)

1. Extension posts {url, title, text} → FastAPI /analyze (request validated by AnalyzeRequest).

2. claims.py runs extract_claims(text, max_claims) using CLAIM_EXTRACTION from config.py.

3. The list of claims flows to later stages (retrieval → NLI) and eventually forms the AnalyzeResponse:

    * claims_checked = len(claims)

    * Each claim will get label/confidence/evidence later.

    * Final article_score/label comes from aggregation settings in config.py.

# Troubleshooting & Environment Notes

* **spaCy wheels vs Python version**: We standardized on Python 3.11 because spaCy 3.7 has mature wheels there. Newer Python (3.13) triggered source builds and failures.
<img width="611" height="101" alt="Error downloading english model spaCy" src="https://github.com/user-attachments/assets/d2393d84-717c-4b97-b1da-e047397b345b" />

* **Install sequence**:
  
        python3.11 -m venv backend/.venv
        source backend/.venv/bin/activate
        python -m pip install -U pip setuptools wheel
        python -m pip install "spacy==3.7.4" "en_core_web_sm==3.7.1"
* **VS Code**: Select the interpreter at backend/.venv/bin/python. If imports show unresolved, reload the window.

# Extensibility (what we can tweak next)

* Tune CLAIM_EXTRACTION to adjust volume/strictness of claims.

* Swap _is_declarative heuristic with a lightweight “claimness” classifier if you want higher precision.

* Add language detection to skip non-English pages before extraction.

* Record char spans (start/end) for claims if you want to highlight them in-page later.


