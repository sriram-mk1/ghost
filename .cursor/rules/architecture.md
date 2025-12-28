# Architecture & High-Value Workflows

## Durable Orchestration (Temporal)
- **State Persistence:** Every browser session state is mapped to a Temporal workflow. If a task takes 3 days, Temporal maintains the state.
- **Signals & Queries:** Use `Signals` to receive Resend webhook approvals and `Queries` to expose the current agent "thought process" to the dashboard.

## Virtual Computer (Steel)
- **Session Persistence:** Map `steel_session_id` to `supabase_user_id`. The agent stays logged in.
- **Manual Handover:** The Next.js dashboard allows the user to "Join Session," take control of the mouse via an embedded session, and then hand it back to the agent.
- **Vision Loop:** Steel screenshots are fed to Gemini Flash to verify UI state.

## HITL Loop (Resend)
1. **Trigger:** Agent identifies a "destructive" or "high-stakes" action.
2. **Pause:** Temporal workflow pauses; `request_human_approval` activity is called.
3. **Webhook:** User clicks "Approve" in email -> Resend calls FastAPI `/webhooks/resend/approve` -> FastAPI sends a Temporal `Signal`.
4. **Resume:** Workflow receives signal and continues.

## Memory Layer (Supermemory)
- **Supermemory API:** Integrated for persistent memory. 
- **User Profiling:** Use Supermemory's profile API to fetch user-specific context and habits before starting a task.
- **Retrieval:** Use `v3/search` for semantic retrieval of relevant SOPs or past document context.
