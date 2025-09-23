# _claim_test.py  # quick smoke test for claim extraction

from app.pipeline.claims import extract_claims     # import the function

article = """
Officials announced on Monday that the city will allocate $12 million to expand public transit in 2025.
According to Reuters, ridership increased by 8% last year across the metro area.
Some residents asked whether fares would be reduced?
The mayor stated the first phase begins in Q3 2024 and creates 120 jobs.
"""

claims = extract_claims(article, max_claims=10)   # run extractor
for i, c in enumerate(claims, 1):                 # print results
    print(i, "-", c)                              # numbered output
