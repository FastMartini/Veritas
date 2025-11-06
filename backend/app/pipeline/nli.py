# nli.py  # temporary stance stub so the pipeline runs end-to-end

from typing import Tuple  # import typing for return annotation

def stance(claim: str, evidence_text: str) -> Tuple[str, float]:
    """
    Return a dummy stance and confidence so the API works.
    Replace with real MNLI later.
    """
    # simple rule: if evidence repeats ≥3 claim words → "supported"
    claim_terms = set(w.lower() for w in claim.split())            # tokenize claim
    evid_terms  = set(w.lower() for w in evidence_text.split())    # tokenize evidence
    overlap = len(claim_terms & evid_terms)                        # compute overlap
    if overlap >= 3:                                               # threshold heuristic
        return "supported", 0.65                                   # label and confidence
    return "unclear", 0.40                                         # default fallback
