from fastapi import FastAPI

# Instantiate the FastAPI application
app = FastAPI(title="Veritas API")

# Health check endpoint to verify server is running
@app.get("/health")
def health_check():
    return {"status": "ok"}
