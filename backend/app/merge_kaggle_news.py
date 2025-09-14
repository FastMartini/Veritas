# merge_kaggle_news.py
# Combine Kaggle True/Fake CSVs into one fakenews.csv with a label column.

from pathlib import Path            # path-safe file handling
import pandas as pd                 # CSV loading and saving

# --- Paths (resolve relative to this file) ---
APP_DIR = Path(__file__).resolve().parent            # .../backend/app
DATA_DIR = APP_DIR.parent / "data"                   # .../backend/data
OUT_CSV  = DATA_DIR / "fakenews.csv"                 # output path

FAKE_CSV = DATA_DIR / "Fake.csv"                     # Kaggle fake file
TRUE_CSV = DATA_DIR / "True.csv"                     # Kaggle real file

def main():
    # Safety checks: make sure the input files exist
    if not FAKE_CSV.exists():
        raise FileNotFoundError(f"Missing file: {FAKE_CSV}")
    if not TRUE_CSV.exists():
        raise FileNotFoundError(f"Missing file: {TRUE_CSV}")

    # Load CSVs
    fake = pd.read_csv(FAKE_CSV)                     # read Fake.csv
    true = pd.read_csv(TRUE_CSV)                     # read True.csv

    # Add labels
    fake["label"] = "FAKE"                           # tag fake rows
    true["label"] = "REAL"                           # tag real rows

    # Keep only title/text/label (Kaggle files have these columns)
    fake = fake[["title", "text", "label"]]
    true = true[["title", "text", "label"]]

    # Concatenate and shuffle (optional but nice)
    df = pd.concat([fake, true], ignore_index=True)  # stack rows
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)  # shuffle

    # Save merged CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)  # ensure data dir
    df.to_csv(OUT_CSV, index=False)                    # write CSV

    # Small preview
    print(f"✅ Saved: {OUT_CSV}  (rows={len(df)})")
    print(df.head(3))

if __name__ == "__main__":
    main()
