# How to Start Veritas (Local Setup)

This guide explains how to run Veritas on your own machine:
- FastAPI backend (claim extraction + Gemini verdict summary)
- Chrome extension popup UI that calls the backend

---

## 1) Prerequisites

Install/confirm:
- Python 3.12+ (recommended)
- Google Chrome (or Chromium-based browser)

You will also need:
- A Gemini API key (stored locally in a `.env` file)

---

## 2) Clone the repo

```bash
git clone <YOUR_REPO_URL>
cd VERITAS
```
---

## 3) Create and Activate a Virtual Environment

### macOS/Linux

```Bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)
```Bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

You should now see:
```Bash
(.venv)
```
inside your terminal prompt

## 4) Install Python Dependencies

Install required packages:
```Bash
pip install --upgrade pip
pip install -r requirements.txt
```
If you do not have a requirements.txt, install manually:
```Bash
pip install fastapi uvicorn spacy python-dotenv python-dateutil google-generativeai
```

## 5) Install spaCy Language Model
Veritas uses spaCy for sentence parsing and claim ranking.
```Bash
python -m spacy download en_core_web_sm
```
If skipped, `/extract` will fail

## 6) Create the `.env` File
In the project root (same folder as `main.py`), create:
```Bash
.env
```
Add:
```Plain text
GOOGLE_API_KEY=PASTE_YOUR_KEY_HERE
GOOGLE_GENAI_USE_VERTEXAI=0
```
### Important:
- .env must live in the same folder as main.py

- Never commit .env to GitHub

- Each developer must use their own API key

## 7) Run the FastAPI Backend

From the project root:
```Bash
uvicorn main:app
```
Backend will run at:
```Bash
http://127.0.0.1:8000
```
Test:
```Bash
http://127.0.0.1:8000/health
```
Expected response:
```JSON
{"status": "ok"}
```
## 8) Load the Chrome Extension

**1.** Open Chrome

**2.** Go to:
```
chrome://extensions
```
**3.** Enable **Developer mode**

**4.** Click **Load unpacked**

**5.** Select the extension folder inside the Veritas project

You should now see the Veritas icon in your toolbar.

## 9) Run an Analysis

**1.** Open a news article in Chrome

**2.** Click the Veritas extension

**3.** Click Analyze Page

All done! Now you are ready to run analyze to your heart's content.