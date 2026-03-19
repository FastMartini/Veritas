# Veritas v0.3.1 – Direct connection to the Gemini API

## Major Features Added

### 1. Direct Gemini AI Integration

The Veritas backend now connects directly to the **Gemini API** using the official `google-genai` client. This replaces the earlier experimental **ADK agent orchestration** (We are no longer reading agent.py), simplifying the architecture. The backend now sends extracted claims directly to Gemini for evaluation.



**Why?**
- At this stage, Veritas only needed one AI action
- Reduced failure points
- Direct calling made the architecture easier to reason about

Switching to direct calling does not block the move to evidence-based fact verdicts later.


### 2. POST /analyze Update

```python

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
```


## Key Improvements Over v.0.3.0

| Feature                      | v0.3.0 | v0.3.1 |
| ---------------------------- | ------ | ------ |
| Claim extraction             | ✔      | ✔      |
| Chrome extension UI          | ✔      | ✔      |
| AI verdict system            | ✖      | ✔      |
| Gemini integration           | ✖      | ✔      |
| Structured analysis endpoint | ✖      | ✔      |
| Secure API key management    | ✖      | ✔      |

