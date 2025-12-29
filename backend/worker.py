import asyncio
from temporalio.worker import Worker
from temporalio.client import Client
from backend.core.config import get_settings
from backend.temporal.workflows import GhostTeammateWorkflow
from backend.temporal.activities import setup_agent_environment, execute_agent_step, log_step

async def main():
    settings = get_settings()
    
    # Connect to Temporal
    client = await Client.connect(settings.TEMPORAL_ADDRESS)
    
    # Run the worker
    worker = Worker(
        client,
        task_queue="ghost-teammate-queue",
        workflows=[GhostTeammateWorkflow],
        activities=[setup_agent_environment, execute_agent_step, log_step],
    )
    
    print("🚀 Ghost Teammate Worker started...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())

