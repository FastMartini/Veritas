# Veritas v0.3.0 – AI Agent Initialization + /analyze Integration

## Overview

Version 0.3.0 introduces agent-backed analysis.  
The backend now forwards extracted claims to an AI agent and returns a structured verdict and summary to the extension UI.

---

## What Changed in v0.3.0

### Added
- AI agent initialization (`agent.py`)
- `/analyze` POST endpoint to submit extracted claims for assessment
- Deterministic claim mapping using `claim_id` in agent output
- UI verdict updates based on `/analyze` response

### Goal
Prove that:
1. Extracted claims can be forwarded to the agent in a stable format.
2. The agent returns deterministic JSON using provided `claim_id`s.
3. The popup can display the returned verdict and summary.

---

## Agent Initialization (agent.py)

The agent is initialized once and configured to return strict JSON output with a verdict, summary, and per-claim assessments.

```python
from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A truth seeker, in pursuit of the truth and nothing but the truth through the analysis of claims.',
    instruction="""
    You are a factual analysis agent.

    You will receive:
    - source
    - publication_date
    - a list of claims (each with id and text)

    You must return JSON in this exact format:

    {
    "verdict": "True | False | Mixed | Misleading | Insufficient",
    "summary": "Short 2-4 sentence explanation",
    "claim_results": [
    {
      "claim_id": "string",
      "assessment": "True | False | Mixed | Misleading | Insufficient",
      "reason": "1-2 sentence explanation"
    }
    ]
    }

    You must reference claim_id exactly as provided.
    Do not omit any claims.
    Return only valid JSON.
    """
)
```
## `/analyze` Endpoint – Agent Invocation Layer

The `/analyze` endpoint connects structured claim extraction to AI-based reasoning.  
It forwards normalized claims to the agent, parses the returned JSON, and responds with a stable verdict summary for the UI.

---

### Implementation

```python
@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):

    # Why: Prepare structured payload so agent reasoning is bounded and explicit.
    agent_input = {
        "source": req.source,
        "publication_date": req.publication_date,
        "claims": [
            {"id": c.id, "text": c.text}
            for c in req.claims
        ],
    }

    # Why: Convert structured input into readable but deterministic prompt.
    prompt = f"""
    Source: {agent_input['source']}
    Publication Date: {agent_input['publication_date']}

    Claims:
    {json.dumps(agent_input['claims'], indent=2)}
    """

    try:
        # Why: ADK invocation must be isolated to prevent crashing FastAPI.
        response = root_agent.run(prompt)

        # ADK returns structured content in response.output
        raw_text = response.output.strip()

        parsed = json.loads(raw_text)

        return AnalyzeResponse(
            ok=True,
            verdict=parsed.get("verdict", "Insufficient"),
            summary=parsed.get("summary", "No summary provided."),
        )

    except Exception as e:
        return AnalyzeResponse(
            ok=True,
            verdict="Insufficient",
            summary=f"Agent error: {str(e)}",
        )


