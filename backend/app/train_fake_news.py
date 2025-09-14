# train_fake_news.py  // trains a baseline model and saves it for serving

import os  # filesystem paths
import json  # save metadata for later reference
import re  # simple text cleaning
import joblib  # save/load trained pipeline
import pandas as pd  # CSV handling
from sklearn.model_selection import train_test_split  # split data
from sklearn.feature_extraction.text import TfidfVectorizer  # text features
from sklearn.linear_model import LogisticRegression  # classifier
from sklearn.pipeline import Pipeline  # chain vectorizer + classifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score  # metrics

# Paths  // point to your merged CSV and output model folder
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # .../backend
DATA_CSV = os.path.join(BASE_DIR, "data", "fakenews.csv")  # merged CSV
MODEL_DIR = os.path.join(BASE_DIR, "model")  # output directory for model files
MODEL_PATH = os.path.join(MODEL_DIR, "veritas_pipeline.joblib")  # pipeline path
META_PATH = os.path.join(MODEL_DIR, "veritas_meta.json")  # metadata path

def basic_clean(text):  # tiny cleaner for consistency
    text = "" if not isinstance(text, str) else text.lower()  # lowercase + guard
    text = re.sub(r"http\S+|www\.\S+", " ", text)  # remove URLs
    text = re.sub(r"\S+@\S+", " ", text)  # remove emails
    text = re.sub(r"[^a-z\s]", " ", text)  # keep letters/spaces only
    text = re.sub(r"\s+", " ", text).strip()  # collapse whitespace
    return text  # cleaned string

# Load data  // expects columns: title, text, label (REAL/FAKE)
df = pd.read_csv(DATA_CSV)  # read merged CSV
df["input_text"] = (df["title"].fillna("") + " " + df["text"].fillna("")).astype(str)  # title+text
df["input_text"] = df["input_text"].apply(basic_clean)  # clean text

# Map labels  // REAL→1, FAKE→0
label_map = {"REAL": 1, "FAKE": 0}  # mapping
df["y"] = df["label"].map(label_map).astype(int)  # numeric labels

# Split  // stratify maintains class balance
X_train, X_test, y_train, y_test = train_test_split(
    df["input_text"].values, df["y"].values, test_size=0.2, random_state=42, stratify=df["y"].values
)

# Build pipeline  // TF-IDF features + Logistic Regression classifier
pipeline = Pipeline(steps=[
    ("tfidf", TfidfVectorizer(ngram_range=(1,2), min_df=2, max_df=0.9, stop_words="english")),  # features
    ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))  # classifier
])

# Train
pipeline.fit(X_train, y_train)  # learn weights and vocabulary

# Evaluate
y_prob = pipeline.predict_proba(X_test)[:, 1]  # probability of REAL
y_pred = (y_prob >= 0.5).astype(int)  # threshold at 0.5
print("Classification report:\n", classification_report(y_test, y_pred, digits=3))  # precision/recall/F1
print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))  # confusion
print("ROC AUC:", round(roc_auc_score(y_test, y_prob), 3))  # ranking quality

# Save artifacts
os.makedirs(MODEL_DIR, exist_ok=True)  # ensure folder
joblib.dump(pipeline, MODEL_PATH)  # save entire pipeline
with open(META_PATH, "w") as f:  # save metadata
    json.dump({"threshold": 0.5, "label_map": label_map, "notes": "tfidf(1,2)+logreg_balanced"}, f, indent=2)

print(f"Saved model → {MODEL_PATH}")  # confirm
print(f"Saved meta  → {META_PATH}")  # confirm
