# Architecture & High-Value Workflows

## Durable Orchestration (Temporal)
- **State Persistence:** Every browser session state is mapped to a Temporal workflow. If a task takes 3 days, Temporal maintains the state.
- **Signals & Queries:** Use `Signals` to receive Resend webhook approvals and `Queries` to expose the current agent "thought process" to the dashboard.

## Virtual Computer (Steel)
- **Session Persistence:** Map `steel_session_id` to `supabase_user_id`. The agent stays logged in.
- **Manual Handover:** The React frontend allows the user to "Join Session," take control of the mouse, and then hand it back to the agent.
- **Multimodal Feedback:** Steel screenshots are fed to Gemini Flash to verify UI state.

## HITL Loop (Resend)
1. **Trigger:** Agent identifies a "destructive" or "high-stakes" action.
2. **Pause:** Temporal workflow pauses; `send_approval_email` activity is called.
3. **Webhook:** User clicks "Approve" in email -> Resend calls FastAPI `/webhooks/resend` -> FastAPI sends a Temporal `Signal`.
4. **Resume:** Workflow receives signal and continues.

## Tiered Memory
- **Short-Term:** Temporal state (current task variables, last few browser steps).
- **Long-Term:** Supabase Vector (pgvector). "Supermemory" stores cross-platform context, user preferences, and standard operating procedures (SOPs).
