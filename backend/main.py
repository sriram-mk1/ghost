from fastapi import FastAPI, Request
from backend.core.config import get_settings

app = FastAPI(title="The Ghost Teammate API")

@app.get("/")
async def root():
    return {"message": "The Ghost Teammate is active."}

@app.post("/webhooks/resend")
async def resend_webhook(request: Request):
    # This will handle inbound emails and approval clicks
    payload = await request.json()
    # Logic to trigger Temporal workflows or signals
    return {"status": "received"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

