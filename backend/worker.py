"""
Temporal Worker
---------------
The process that executes workflows and activities.
Run this alongside the FastAPI server to process tasks.

Usage:
    cd /path/to/ghost
    export PYTHONPATH=$PYTHONPATH:$(pwd)
    source venv/bin/activate
    python -m backend.worker
"""
import asyncio
from temporalio.worker import Worker
from temporalio.client import Client
from backend.core.config import get_settings
from backend.temporal.workflows import GhostTeammateWorkflow
from backend.temporal.activities import (
    create_job_record,
    agent_strategic_planning,
    provision_browser_environment,
    execute_agent_turn,
    request_approval_activity,
    update_job_status,
    send_completion_email,
    save_task_memory,
    release_browser_session,
)


async def main():
    """
    Main entry point for the Temporal worker.
    Connects to Temporal server and starts processing tasks.
    """
    settings = get_settings()
    
    print("🔌 Connecting to Temporal server...")
    print(f"   Address: {settings.TEMPORAL_ADDRESS}")
    
    client = await Client.connect(settings.TEMPORAL_ADDRESS)
    
    # Create the worker with all workflows and activities
    worker = Worker(
        client,
        task_queue="ghost-teammate-queue",
        workflows=[GhostTeammateWorkflow],
        activities=[
            create_job_record,
            agent_strategic_planning,
            provision_browser_environment,
            execute_agent_turn,
            request_approval_activity,
            update_job_status,
            send_completion_email,
            save_task_memory,
            release_browser_session,
        ],
    )
    
    # List of registered activities (for logging)
    activity_names = [
        "create_job_record",
        "agent_strategic_planning", 
        "provision_browser_environment",
        "execute_agent_turn",
        "request_approval_activity",
        "update_job_status",
        "send_completion_email",
        "save_task_memory",
        "release_browser_session",
    ]
    
    print("")
    print("=" * 50)
    print("🚀 Ghost Teammate Worker Started")
    print("=" * 50)
    print(f"   Task Queue: ghost-teammate-queue")
    print(f"   Workflows:  GhostTeammateWorkflow")
    print(f"   Activities: {len(activity_names)} registered")
    print("")
    print("   Registered Activities:")
    for name in activity_names:
        print(f"     • {name}")
    print("")
    print("   Press Ctrl+C to stop.")
    print("=" * 50)
    print("")
    
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
