# The Ghost Teammate: Project Overview

## Core Mission
A proactive, headless AI agent that acts as a remote teammate. It is invited to workspaces (Notion, Google Docs, etc.) as a dedicated "Teammate" account. It interacts via browser automation (Steel) and communicates primarily through native app features (@mentions, comments) and high-value emails (Resend).

## Core Pillars
1. **Headless Sovereignty:** The agent has its own account identity. It is a collaborator, not a proxy for the user's credentials.
2. **Durable Orchestration (Temporal):** Long-running tasks that can pause for days while waiting for human input, with zero state loss.
3. **Virtual Computer (Steel):** Physical UI interaction instead of brittle API calls. "Hands and Eyes" for the agent.
4. **Human-in-the-Loop (HITL) Safety:** Hard-coded safety for destructive actions (Delete/Pay) via Resend approvals.
5. **Native Interaction:** Conversations live where the work happens (Notion comments, Google Doc edits).

## Tech Stack
- **Orchestration:** Temporal (Durable execution).
- **Brain:** Gemini 3 (Flash for vision/fast UI loops, Pro for complex planning).
- **Communication:** Resend (Email/Webhooks) + Steel (In-app comments).
- **Hands:** Steel (Cloud-based browser automation).
- **Database:** Supabase (Auth, Vector Memory, Logs).
- **Backend:** Python (FastAPI).
- **Frontend:** React (Dashboard + Steel "Live View").
