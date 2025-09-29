# config.py  # central configuration for Veritas backend

# ---------- Trusted sources (allowlist) ----------
# These domains are considered reliable for evidence retrieval.
# Expand this list as your project matures or make it environment-driven later.
TRUSTED_SITES = [
    # General News
    "apnews.com",          # Associated Press
    "reuters.com",         # Reuters
    "bbc.com",             # BBC News
    "npr.org",             # NPR

    # Fact-Checking
    "snopes.com",          # Snopes
    "politifact.com",      # PolitiFact
    "factcheck.org",       # FactCheck.org

    # Research & Reference
    "pewresearch.org",     # Pew Research Center
    "propublica.org",      # ProPublica
    "theconversation.com", # The Conversation

    # Major International News
    "economist.com",       # The Economist
    "aljazeera.com",       # Al Jazeera English
    "dw.com",              # Deutsche Welle

    # Science & Health
    "nature.com",          # Nature Journal
    "science.org",         # Science Journal
    "nih.gov",             # National Institutes of Health
    "cdc.gov",             # Centers for Disease Control and Prevention

    # Data & Policy
    "worldbank.org",       # World Bank
    "oecd.org",            # OECD
    "un.org",              # United Nations
    "data.un.org",         # UN Data
    "undp.org",            # UN Development Programme
    "crsreports.congress.gov", # Congressional Research Service

    # Investigative & Nonprofit
    "publicintegrity.org", # Center for Public Integrity
    "icij.org",           # International Consortium of Investigative Journalists


    # U.S. Government – General Info & Data
    "usa.gov",            # U.S. government portal
    "data.gov",           # Open government data
    "congress.gov",       # U.S. Congress info

    # U.S. Government – Science & Research
    "nasa.gov",           # NASA
    "noaa.gov",           # National Oceanic & Atmospheric Administration
    "usgs.gov",           # U.S. Geological Survey
    "nsf.gov",            # National Science Foundation

    # U.S. Government – Health & Safety
    "fda.gov",            # Food and Drug Administration
    "healthdata.gov",     # Public health datasets

    # U.S. Government – Economy & Statistics
    "bea.gov",            # Bureau of Economic Analysis
    "bls.gov",            # Bureau of Labor Statistics
    "census.gov",         # U.S. Census Bureau
    "federalreserve.gov", # U.S. Federal Reserve

    # U.S. Government – Law & Justice
    "supremecourt.gov",   # Supreme Court of the United States
    "justice.gov",        # Department of Justice

    # U.S. Government – International & Security
    "state.gov",          # U.S. Department of State
    "defense.gov",        # U.S. Department of Defense
    "cia.gov",            # CIA World Factbook
]

# ---------- Aggregation thresholds ----------
# We map the aggregated article score (0..1) to a label shown in the UI.
AGGREGATION = {
    "high_min": 0.75,  # scores >= 0.75 → "High" credibility
    "med_min": 0.55,   # scores in [0.55, 0.75) → "Medium"; else "Low"
}

# ---------- Extraction defaults ----------
# Heuristics for claim extraction (used by the extractor to limit noise).
CLAIM_EXTRACTION = {
    "max_claims": 12,          # upper bound of claims per article
    "min_tokens": 8,           # skip sentences shorter than this
    "max_tokens": 40,          # skip very long/rambling sentences
    "require_entity_or_digit": True,  # keep sentences with a named entity OR a number/date
}

# ---------- Retrieval settings ----------
# Used by the retrieval layer to control breadth/depth of search.
RETRIEVAL = {
    "top_k_docs": 5,           # how many documents to fetch initially
    "top_k_snippets": 3,       # evidence snippets kept per claim (before re-rank)
    "timeout_s": 8,            # network timeout for each search/fetch
}

# ---------- Re-ranking settings ----------
# Placeholder knobs for embedding re-rank (when you add sentence-transformers).
RERANK = {
    "use_embeddings": False,   # set True when MiniLM or similar is added
    "top_k_final": 2,          # after re-rank, keep this many best snippets
}

# ---------- NLI (stance) settings ----------
# Confidence thresholds for supported/refuted/unclear classification.
NLI = {
    "model_name": "roberta-large-mnli",  # planned HF model (placeholder until implemented)
    "min_confidence": 0.6,               # below this, downgrade to 'unclear'
}

# ---------- Caching ----------
# Simple knobs for URL→result cache to avoid reprocessing the same page.
CACHE = {
    "enabled": True,            # enable in-memory cache (swap with Redis later if needed)
    "ttl_seconds": 3600,        # time-to-live per URL result (1 hour)
    "max_entries": 500,         # simple bound to keep memory reasonable
}