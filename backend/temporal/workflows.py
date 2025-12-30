"""
Ghost Teammate Workflow
-----------------------
The main Temporal workflow that orchestrates the agent's lifecycle.

This is the "durable orchestration" layer that:
1. Persists state across interruptions (can sleep for days)
2. Handles Human-in-the-Loop approvals
3. Coordinates activities in the correct order
4. Provides exactly-once execution guarantees
"""
from datetime import timedelta
from temporalio import workflow

# Import activities through the unsafe passthrough
# (Required because activities use async I/O which isn't allowed in workflow code)
with workflow.unsafe.imports_passed_through():
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


@workflow.defn
class GhostTeammateWorkflow:
    """
    The main workflow for handling user tasks.
    
    Triggered by:
    - Inbound email to assistant+{user_id}@domain.com
    - API call from the dashboard
    
    Lifecycle:
    1. Create job record (tracking)
    2. Strategic planning (should we use browser?)
    3. If BROWSER: provision session → execute turns → complete
    4. If MEMORY: respond directly from context
    5. If CLARIFY: ask user for more info
    6. Save to memory for future context
    
    Mid-Task Communication:
    - Users can send additional emails mid-task
    - These are injected via the `user_message` signal
    - The agent incorporates them into its next reasoning step
    """
    
    def __init__(self):
        # Signal state for Human-in-the-Loop approvals
        self._approved: bool | None = None
        # Queue for mid-task user messages (email replies)
        self._user_messages: list[str] = []
        # Flag for kill switch
        self._killed: bool = False

    @workflow.signal
    def approve(self):
        """Signal sent when user clicks 'Approve' in email."""
        self._approved = True

    @workflow.signal
    def reject(self):
        """Signal sent when user clicks 'Reject' in email."""
        self._approved = False
    
    @workflow.signal
    def user_message(self, message: str):
        """
        Signal sent when user replies to the agent's email mid-task.
        The message is queued and incorporated into the agent's next turn.
        """
        self._user_messages.append(message)
    
    @workflow.signal
    def kill(self):
        """
        Kill switch - immediately stops the workflow.
        Used from the dashboard when user wants to abort a task.
        """
        self._killed = True
    
    @workflow.query
    def get_status(self) -> dict:
        """
        Query the current workflow status.
        Can be called from the dashboard to get live updates.
        """
        return {
            "approved": self._approved,
            "pending_messages": len(self._user_messages),
            "killed": self._killed,
        }

    @workflow.run
    async def run(self, goal: str, user_id: str, user_email: str) -> str:
        """
        Main workflow execution.
        
        Args:
            goal: The user's task/request
            user_id: Unique user identifier
            user_email: Email to send updates to
            
        Returns:
            Final status message
        """
        session_id = None  # Track for cleanup
        
        try:
            # ============================================
            # STEP 1: Initialize Job Tracking
            # ============================================
            job_id = await workflow.execute_activity(
                create_job_record,
                args=[user_id, goal],
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            # ============================================
            # STEP 2: Strategic Planning (Memory-First)
            # ============================================
            plan = await workflow.execute_activity(
                agent_strategic_planning,
                args=[user_id, goal],
                start_to_close_timeout=timedelta(minutes=2)
            )
            
            strategy = plan["strategy"]
            profile = plan["profile"]
            
            # ============================================
            # STEP 3: Execute Based on Strategy
            # ============================================
            
            if strategy == "BROWSER":
                # --- BROWSER STRATEGY ---
                # Agent needs to interact with a web application
                
                # 3a. Provision the virtual computer
                session_id = await workflow.execute_activity(
                    provision_browser_environment,
                    args=[user_id, job_id],
                    start_to_close_timeout=timedelta(minutes=3)
                )
                
                # 3b. Execute reasoning-action loop (max 20 turns)
                final_reasoning = ""
                current_goal = goal  # Can be modified by user messages
                
                for turn in range(20):
                    # ========================================
                    # CHECK KILL SWITCH
                    # ========================================
                    if self._killed:
                        await workflow.execute_activity(
                            update_job_status,
                            args=[job_id, "killed"],
                            start_to_close_timeout=timedelta(seconds=10)
                        )
                        return "Task killed by user."
                    
                    # ========================================
                    # CHECK FOR MID-TASK USER MESSAGES
                    # ========================================
                    if self._user_messages:
                        # Incorporate all pending messages into the goal
                        user_additions = "\n\n--- USER UPDATE ---\n" + "\n".join(self._user_messages)
                        current_goal = goal + user_additions
                        self._user_messages.clear()
                    
                    result = await workflow.execute_activity(
                        execute_agent_turn,
                        args=[session_id, current_goal, user_id, profile, job_id],
                        start_to_close_timeout=timedelta(minutes=5)
                    )
                    
                    final_reasoning = result.get("reasoning", "")
                    
                    # ========================================
                    # HITL SAFETY GATE (from activity or keywords)
                    # ========================================
                    needs_approval = result.get("requires_approval", False)
                    approval_action = result.get("approval_action", "")
                    
                    # Also check keywords in reasoning
                    reasoning_upper = final_reasoning.upper()
                    keyword_triggered = any(keyword in reasoning_upper for keyword in [
                        "DELETE", "REMOVE", "PAY", "PURCHASE", "SUBMIT", 
                        "CONFIRM ORDER", "SEND PAYMENT", "PERMANENTLY",
                        "IRREVERSIBLE", "CHECKOUT", "PLACE ORDER"
                    ])
                    
                    if needs_approval or keyword_triggered:
                        # Update status
                        await workflow.execute_activity(
                            update_job_status,
                            args=[job_id, "waiting_approval"],
                            start_to_close_timeout=timedelta(seconds=10)
                        )
                        
                        # Send approval email
                        await workflow.execute_activity(
                            request_approval_activity,
                            args=[user_email, user_id, workflow.info().workflow_id, approval_action or final_reasoning],
                            start_to_close_timeout=timedelta(minutes=1)
                        )
                        
                        # PAUSE: Wait for user signal (max 24 hours)
                        # Also wake up if killed
                        await workflow.wait_condition(
                            lambda: self._approved is not None or self._killed,
                            timeout=timedelta(hours=24)
                        )
                        
                        if self._killed:
                            await workflow.execute_activity(
                                update_job_status,
                                args=[job_id, "killed"],
                                start_to_close_timeout=timedelta(seconds=10)
                            )
                            return "Task killed by user."
                        
                        if self._approved is False:
                            # User rejected
                            await workflow.execute_activity(
                                update_job_status,
                                args=[job_id, "rejected"],
                                start_to_close_timeout=timedelta(seconds=10)
                            )
                            return "Task aborted: User rejected the high-stakes action."
                        
                        # User approved - continue
                        self._approved = None
                        
                        await workflow.execute_activity(
                            update_job_status,
                            args=[job_id, "running"],
                            start_to_close_timeout=timedelta(seconds=10)
                        )
                    
                    # Check if agent finished
                    if result.get("finished", False):
                        break
                
                # 3c. Complete and notify
                await workflow.execute_activity(
                    update_job_status,
                    args=[job_id, "completed"],
                    start_to_close_timeout=timedelta(seconds=10)
                )
                
                await workflow.execute_activity(
                    send_completion_email,
                    args=[user_email, user_id, goal, final_reasoning],
                    start_to_close_timeout=timedelta(seconds=30)
                )
                
                # Save to memory
                await workflow.execute_activity(
                    save_task_memory,
                    args=[user_id, goal, final_reasoning],
                    start_to_close_timeout=timedelta(seconds=30)
                )
                
                return f"Task completed via virtual computer. Summary: {final_reasoning[:200]}"
            
            elif strategy == "CLARIFY":
                # --- CLARIFY STRATEGY ---
                await workflow.execute_activity(
                    update_job_status,
                    args=[job_id, "waiting_info"],
                    start_to_close_timeout=timedelta(seconds=10)
                )
                
                # TODO: Send clarification email
                return f"Agent needs clarification: {plan['reasoning']}"
            
            else:
                # --- MEMORY STRATEGY ---
                await workflow.execute_activity(
                    update_job_status,
                    args=[job_id, "completed"],
                    start_to_close_timeout=timedelta(seconds=10)
                )
                
                await workflow.execute_activity(
                    send_completion_email,
                    args=[user_email, user_id, goal, plan['reasoning']],
                    start_to_close_timeout=timedelta(seconds=30)
                )
                
                # Save to memory
                await workflow.execute_activity(
                    save_task_memory,
                    args=[user_id, goal, plan['reasoning']],
                    start_to_close_timeout=timedelta(seconds=30)
                )
                
                return f"Resolved from memory: {plan['reasoning']}"
                
        finally:
            # ============================================
            # CLEANUP: Release browser session
            # ============================================
            if session_id:
                try:
                    await workflow.execute_activity(
                        release_browser_session,
                        args=[session_id],
                        start_to_close_timeout=timedelta(seconds=30)
                    )
                except Exception:
                    pass  # Best effort cleanup
