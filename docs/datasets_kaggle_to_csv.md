# Dataset Setup Guide (Kaggle ➜ fakenews.csv with Git LFS)
This guide documents how we obtained our dataset from Kaggle, merged it into a single CSV file (fakenews.csv), and set up our Python environment for training. It also explains why we decided to use Git Large File Storage (LFS) to manage dataset files in GitHub.

# 0) Repo Layout (Target)

<img width="614" height="355" alt="Screenshot 2025-09-10 at 3 38 41 AM" src="https://github.com/user-attachments/assets/6a732894-5786-43e6-a7b2-50bbbd87c153" />

# 1) Why We Use Git LFS & How To Set Up

We attempted to commit three CSVs to GitHub:

- backend/data/True.csv → ~51.10 MB (GitHub warns above 50 MB)

- backend/data/Fake.csv → ~59.88 MB (warning above 50 MB)

- backend/data/fakenews.csv → ~109.97 MB (hard block at 100 MB)

Because our merged dataset is ~110 MB, normal Git pushes were blocked. We chose Git LFS so we can keep these files in the repo without hitting Git’s 100 MB barrier. We initially considered ignoring large CSVs in Git and storing them locally or in Google Drive. However, two factors made Git LFS the better option for this project:

- **Deadlines**: This is a small capstone project with strict time constraints. Git LFS allows us to keep datasets directly in the repo, so every collaborator can clone and run scripts immediately without manual setup.

- **Collaboration**: With multiple collaborators, storing datasets externally would lead to sync issues, outdated files, or broken paths. Git LFS solves this by versioning large files alongside our code.

_**For help on how to set up Git LFS visit their official site: https://git-lfs.com/**_

# 2) Get the Dataset from Kaggle
1. Go to https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset.
2. Download the ZIP file.
3. Extract it and move Fake.csv and True.csv into backend/data/.

# 3) Setup Python Environment

On the terminal, enter the following lines in their respective order:

<img width="607" height="284" alt="Screenshot 2025-09-10 at 3 54 28 AM" src="https://github.com/user-attachments/assets/d3003a1f-0452-4d85-8458-6e453b3e2cf4" />


Since we are utilizing **VS Code**, we made sure to do the following: Cmd+Shift+P → Python: Select Interpreter → veritas/backend/.venv/bin/python

_This allows VS Code to use .venv in our enviornment with our dependencies._

# 4) Merge Kaggle Files Into fakenews.csv

1) After downloading from Kaggle, we have two files in backend/data/:
     - backend/data.Fake.csv
    - backend/data/True.csv

2) Both contain columns like: title, text, subject, date. We'll add a label (FAKE or REAL), we will keep only the columns our training script needs (title, text, label). Results should look like this:
    - backend/data/fakenews.csv

3) Before making the script, create this file at:
    - backend/app/merge_kaggle_news.py

<img width="477" height="691" alt="Screenshot 2025-09-10 at 4 18 55 AM" src="https://github.com/user-attachments/assets/94aa9527-54fd-4c13-af7a-f16a9b4766e5" />



**First lines of the script:**

    from pathlib import Path
    import pandas as pd

This imports the libraries. Path from the pathlib module lets us work with file paths in a clean, cross-platform way. pandas is imported as pd, which is the standard alias. Pandas is what we use to load and manipulate CSV files as tables (DataFrames).

**Setting up project paths:**

    APP_DIR  = Path(__file__).resolve().parent
    DATA_DIR = APP_DIR.parent / "data"

Here we are finding the location of the script itself using __file__. resolve().parent gives us the folder where merge_kaggle_news.py lives, which should be backend/app. From there, .parent moves up one directory to backend, and then we add /data to point to the dataset folder. This way the script works no matter where you run it from.

**Checking that the files exist:**

    if not FAKE_CSV.exists():
      raise FileNotFoundError(f"Missing file: {FAKE_CSV}")
    if not TRUE_CSV.exists():
      raise FileNotFoundError(f"Missing file: {TRUE_CSV}")

Before loading anything, the script checks if Fake.csv and True.csv actually exist in the backend/data folder. If they don’t, the script will raise a clear error telling you which file is missing.

**Loading the CSVs into DataFrames:**

    fake = pd.read_csv(FAKE_CSV)
    true = pd.read_csv(TRUE_CSV)

These lines use pandas.read_csv to load each file into a DataFrame. Now fake holds all of the fake news rows, and true holds all of the real news rows.

**Validating expected columns:**

    required_cols = {"title", "text"}
    missing_in_fake = required_cols - set(fake.columns)
    missing_in_true = required_cols - set(true.columns)
    if missing_in_fake:
      raise ValueError(f"Fake.csv missing columns: {missing_in_fake}")
    if missing_in_true:
      raise ValueError(f"True.csv missing columns: {missing_in_true}")

We check that both CSVs contain the columns title and text, which our training script depends on. If either file is missing those columns, the script raises a clear error explaining which ones are missing.

**Adding the label column:**

    fake["label"] = "FAKE"
    true["label"] = "REAL"
A new column called label is added to both DataFrames. Every row in fake is tagged with "FAKE" and every row in true is tagged with "REAL". This is what lets the model later know which rows are real and which are fake. 

**Keeping only the relevant columns:**

    fake = fake[["title", "text", "label"]]
    true = true[["title", "text", "label"]]
Each DataFrame may have extra columns like subject or date, but we only keep title, text, and label. This keeps the dataset consistent and small.

**Combining the datasets:**

    df = pd.concat([fake, true], ignore_index=True)
Here we stack the fake and true DataFrames into one big DataFrame called df. The ignore_index=True makes sure the new DataFrame is reindexed from 0 to N-1.

**Shuffling the rows:**

    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
  This takes the combined DataFrame and shuffles all rows randomly. frac=1.0 means use the whole dataset, and random_state=42 ensures the shuffle is reproducible. Then we reset the index so it runs from 0 to N-1 again. This prevents all fake or all real rows from being grouped together.

  **Saving the merged file:**

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

  First we make sure the output folder (backend/data) exists. Then we save the DataFrame to a CSV file called fakenews.csv. The index=False means we don’t write the Pandas index column into the CSV.

  **Printing a summary for the user:**

    print(f"✅ Saved merged dataset → {OUT_CSV} (rows={len(df)})")
    print("Preview:")
    print(df.head(5))
    print(df["label"].value_counts())

  This prints confirmation that the file was saved, how many rows it has, shows the first five rows as a preview, and prints a count of how many REAL and FAKE rows there are.

  **How to run it (exact commands):**
  
  macOS/Linux:

    # from repo root
    source backend/.venv/bin/activate           # activate your venv (Step 2)
    python backend/app/merge_kaggle_news.py     # run the merge

  Windows (PowerShell):

    # from repo root
    .\backend\.venv\Scripts\Activate            # activate your venv (Step 2)
    python backend\app\merge_kaggle_news.py     # run the merge

# 5) Expected Output:
  <img width="668" height="64" alt="Screenshot 2025-09-10 at 4 43 32 AM" src="https://github.com/user-attachments/assets/78880330-2d79-43eb-834e-c675b8c714ac" />


  



