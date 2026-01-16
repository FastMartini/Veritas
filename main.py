from fastapi import FastAPI
from fastapi import Body

# Instantiate the FastAPI application
app = FastAPI(title="Veritas API")

# Health check endpoint to verify server is running
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/analyze")
def analyze(payload: dict = Body(...)):
    
    return {
        "ok": True,
        "received_keys": list(payload.keys())
    }
