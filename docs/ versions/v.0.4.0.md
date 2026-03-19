# Veritas v0.4.0 - Shift to Political Bias Analysis

---

## Overview

Version 0.4.0 marks a fundamental shift in Veritas’s analytical approach.  
The system has transitioned from **truth verification** to **political bias analysis**.

Previously, Veritas attempted to determine whether claims were true or false. This required external validation, cross-referencing sources, and complex reasoning about factual accuracy. In v0.4.0, the system instead evaluates how an article is **framed**, focusing on **editorial leaning** rather than factual correctness.

The result is a faster, more scalable, and fully self-contained analysis pipeline.

---

## Key Changes

### 1. Verdict System Redesign

**Before (v0.3.x):**
- True  
- False  
- Mixed  
- Misleading  
- Insufficient  

**After (v0.4.0):**
- Left-leaning  
- Center-left  
- Center  
- Center-right  
- Right-leaning  
- Unclear  

This change removes the need for external verification and reframes the system as a **bias detection engine**.

---

### 2. Introduction of Bias Signals

The analysis now produces structured numeric signals:

| Signal          | Description |
|----------------|------------|
| `source_bias`  | Bias associated with the publisher or domain |
| `language_bias`| Bias in wording, tone, and emotional language |
| `framing_bias` | Bias in narrative structure and selective emphasis |
| `confidence`   | Strength of the detected bias |

#### Scale

All bias signals follow a standardized range:

```text
-1.0  → strongly left-leaning
 0.0  → neutral / balanced / unclear
+1.0  → strongly right-leaning

```
---
### 3. Prompt Redesign

The Gemini prompt was rewritten to enforce bias analysis and eliminate truth-based outputs.

```Python

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

```
---
### 4. Frontend Updates

- Verdict pill now reflects political leaning

- Added Bias Signals section:

    - Confidence (%)

    - Source bias

    - Language bias

    - Framing bias

- Dynamic styling for:

    - Left (blue)

    - Center (neutral)

    - Right (red)

    - Unclear (gray)

---
## How Bias is Evaluated
The system uses LLM-based heuristic analysis, structured into numeric signals.

### 1. Source Bias

Evaluates:

- Publisher reputation

- Historical ideological alignment

- Institutional tone

**Example:**

New York Times → typically center-left → negative value

### 2. Language Bias

Evaluates:

- Word choice (neutral vs loaded)

- Emotional tone

- Descriptive intensity

**Example:**

Words like “dangerous” or “destabilizing” increase directional bias

### 3. Framing Bias

Evaluates:

- Narrative structure

- Inclusion vs omission of facts

- Portrayal of individuals or groups

This is typically the **strongest** signal.

### 4. Confidence

Represents:

- Consistency of bias signals

- Clarity of narrative direction

= Strength of evidence within the text

### 5. Verdict Derivation

The verdict corresponds to the overall directional tendency of the signals.

Conceptually:

```text
average_bias ≈ (source_bias + language_bias + framing_bias) / 3
```

Mapped to categories:

| Range          | Verdict       |
| -------------- | ------------- |
| -1.0 to -0.75  | Left-leaning  |
| -0.75 to -0.25 | Center-left   |
| -0.25 to 0.25  | Center        |
| 0.25 to 0.75   | Center-right  |
| 0.75 to 1.0    | Right-leaning |

---
## Strengths and Limitations

### Strengths

#### 1. Fully Self-Contained

- No external APIs or fact-checking sources required

- Works directly from article text

#### 2. Fast and Scalable

- Eliminates expensive verification pipelines

- Suitable for real-time analysis

#### 3. Explainable Output

- Users see why an article leans a certain way

- Transparent signal breakdown

#### 4. Modular Design

- New signals can be added easily

- Backend can later compute verdict independently

### Limitations

#### 1. Not a Factual Accuracy System

- Does not determine truth or falsehood

- Only analyzes framing and tone

#### 2. LLM Subjectivity

- Outputs are based on model reasoning, not statistical calibration

- Same article may yield slightly different scores across runs

#### 3. No Ground Truth Dataset

- Signals are not trained on labeled bias datasets

- No formal validation or benchmarking yet

#### 4. Source Bias Generalization

- Assumes known media tendencies

- May misclassify unfamiliar or niche sources