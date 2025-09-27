# backend/app/pipeline/retrieve.py
from typing import List
import re, math
import httpx
from bs4 import BeautifulSoup

try:
    import readability  # from readability-lxml
except Exception:
    readability = None

from ..schemas import EvidenceSnippet
from .search import google_cse_search
from ..config import RETRIEVAL, TRUSTED_SITES

_WORDS = re.compile(r"[A-Za-z0-9%]+")

def _clean_text(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "")).strip()

def _extract_main_text(html: str) -> str:
    if readability:
        doc = readability.Document(html)
        summary_html = doc.summary(html_partial=True)
        text = BeautifulSoup(summary_html, "html.parser").get_text(" ", strip=True)
    else:
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    return _clean_text(text)

def _overlap_score(a: str, b: str) -> float:
    A = set(w.lower() for w in _WORDS.findall(a))
    B = set(w.lower() for w in _WORDS.findall(b))
    if not A or not B:
        return 0.0
    inter = len(A & B)
    return inter / math.sqrt(len(A) * len(B))

def _best_snippet(claim: str, page_text: str, window_chars: int = 420) -> str:
    low = page_text.lower()
    for k in _WORDS.findall(claim):
        pos = low.find(k.lower())
        if pos >= 0:
            start = max(0, pos - window_chars // 2)
            return page_text[start:start + window_chars]
    return page_text[:window_chars]

def fetch_snippets_for_claim(claim: str) -> List[EvidenceSnippet]:
    hits = google_cse_search(claim, num=RETRIEVAL["top_k_docs"])
    out: List[EvidenceSnippet] = []
    if not hits:
        return out

    headers = {"User-Agent": "Veritas/0.1"}
    with httpx.Client(timeout=RETRIEVAL["timeout_s"], headers=headers) as client:
        for h in hits:
            url = h["url"]
            if not url or not any(d in url for d in TRUSTED_SITES):
                continue
            try:
                html = client.get(url).text
                text = _extract_main_text(html)
                if not text or len(text) < 300:
                    continue
                snippet = _best_snippet(claim, text)
                score = _overlap_score(claim, snippet)
                if score <= 0:
                    continue
                out.append(EvidenceSnippet(
                    snippet=snippet[:430],
                    source=url,
                    retrieval_score=min(1.0, float(score)),
                ))
            except Exception:
                continue

    out.sort(key=lambda s: s.retrieval_score, reverse=True)
    return out[:RETRIEVAL["top_k_snippets"]]

