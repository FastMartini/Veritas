# claims.py  # extract factual-sounding claims from article text using spaCy

from typing import List, Tuple                                              # typing helpers
import re                                                                   # regex for simple cleanup
import spacy                                                                # spaCy NLP library
from app.config import CLAIM_EXTRACTION                                    # knobs from config.py

# Load spaCy model once at import time (fast thereafter)                    # avoid reloading per request
_NLP = spacy.load("en_core_web_sm")                                         # small English pipeline (sentencizer + NER)

def _clean(text: str) -> str:                                               # tiny normalizer for noisy pages
    text = re.sub(r"\s+", " ", text).strip()                                # collapse whitespace
    return text                                                             # return cleaned string

def _token_len(span_text: str) -> int:                                      # count tokens (rough heuristic)
    return len(span_text.split())                                           # whitespace tokenization is enough here

def _has_named_entity(sent) -> bool:                                        # check if sentence mentions entities
    return any(ent.label_ in {"PERSON","ORG","GPE","LOC","DATE","TIME","MONEY","PERCENT"} for ent in sent.ents)

def _has_numeric_fact(sent_text: str) -> bool:                              # check if numbers/dates are present
    return bool(re.search(r"\d", sent_text)) or "%" in sent_text            # digit or percent sign

def _is_declarative(sent_text: str) -> bool:                                # filter out questions/commands
    s = sent_text.strip()                                                   # trim edges
    if s.endswith("?"):                                                     # questions are usually not claims to verify
        return False                                                        # reject questions
    # simple cue words to prefer factual tone                               
    cues = ("reported","announced","according to","stated","published","confirmed","data shows")
    return any(cue in s.lower() for cue in cues) or True                    # weak prior: allow most sentences

def _salience(sent, idx: int) -> float:                                # idx = sentence position
    score = 0.0                                                        # base score
    tl = _token_len(sent.text)                                         # token length
    if 8 <= tl <= 40:                                                  # prefer concise claims
        score += 0.4                                                   # add weight
    score += 0.35 if _has_named_entity(sent) else 0.0                  # entities help
    score += 0.15 if _has_numeric_fact(sent.text) else 0.0             # numbers help
    score += 0.1 if idx <= 5 else 0.0                                  # early sentence bonus
    return max(0.0, min(1.0, score))                                   # clamp to [0,1]

def extract_claims(text: str, max_claims: int = None) -> List[str]:
    cfg = CLAIM_EXTRACTION                                             # read config
    cap = max_claims or cfg["max_claims"]                              # cap results
    doc = _NLP(_clean(text))                                           # run NLP

    candidates: List[Tuple[float, str]] = []                           # (salience, text)
    for idx, sent in enumerate(doc.sents):                             # idx = sentence order
        tl = _token_len(sent.text)                                     # length check
        if tl < cfg["min_tokens"] or tl > cfg["max_tokens"]:           # skip extremes
            continue
        if cfg["require_entity_or_digit"] and not (                    # gate by entity/number
            _has_named_entity(sent) or _has_numeric_fact(sent.text)
        ):
            continue
        if not _is_declarative(sent.text):                             # skip questions/commands
            continue
        candidates.append((_salience(sent, idx), sent.text.strip()))   # score with idx

    if not candidates:                                                 # none found
        return []

    seen = set()                                                       # dedupe
    unique: List[Tuple[float, str]] = []
    for score, s in sorted(candidates, key=lambda x: x[0], reverse=True):
        key = re.sub(r"\W+", " ", s.lower()).strip()                   # normalize
        if key in seen:
            continue
        seen.add(key)
        unique.append((score, s))

    return [s for _, s in unique[:cap]]                                # top-k                                                               # list of claim strings
