from fastapi import FastAPI, Request, HTTPException
from temporalio.client import Client
import uuid
from backend.core.config import get_settings
from backend.temporal.workflows import GhostTeammateWorkflow

app = FastAPI(title="The Ghost Teammate API")
settings = get_settings()

@app.get("/")
async def root():
    return {"message": "The Ghost Teammate is active."}

@app.post("/tasks/launch")
async def launch_task(goal: str, user_id: str):
    """API endpoint to start up the agent durable workflow"""
    try:
        # Connect to Temporal
        client = await Client.connect(settings.TEMPORAL_ADDRESS)

        # Unique workflow ID per task
        workflow_id = f"teammate-{uuid.uuid4()}"

        # Start the durable workflow
        await client.start_workflow(
            GhostTeammateWorkflow.run,
            args=[goal, user_id],
            id=workflow_id,
            task_queue="ghost-teammate-queue",
        )

        return {"id": workflow_id, "status": "launched"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/resend")
async def resend_webhook(request: Request):
    # This will handle inbound emails and approval clicks
    payload = await request.json()
    # Logic to trigger Temporal workflows or signals
    return {"status": "received"}

@app.get("/webhooks/resend/approve")
async def approve_task(workflow_id: str):
    client = await Client.connect(settings.TEMPORAL_ADDRESS)
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal("approve")
    return {"status": "Workflow approved"}

@app.get("/webhooks/resend/reject")
async def reject_task(workflow_id: str):
    client = await Client.connect(settings.TEMPORAL_ADDRESS)
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal("reject")
    return {"status": "Workflow rejected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
