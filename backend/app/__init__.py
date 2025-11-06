# app/__init__.py
from pathlib import Path                    # filesystem helper
from dotenv import load_dotenv              # env loader

_BASE = Path(__file__).resolve().parent     # path to app/
load_dotenv(_BASE / ".env")                 # load app/.env explicitly

