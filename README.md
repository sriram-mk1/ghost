# The Ghost Teammate: Project Overview

## Core Mission
A proactive, headless AI agent that acts as a remote teammate. It lives in the user's workflow via Email (Resend) and interacts with collaborative SaaS tools (Notion, Google Workspace, Linear, etc.) using a virtual computer (Steel).

## Tech Stack
- **Orchestration:** Temporal (Durable execution, HITL).
- **Brain:** Gemini 3 (Flash for speed, Pro for complex reasoning).
- **Communication:** Resend (Email API + Inbound Webhooks).
- **Hands:** Steel (Headless browser automation).
- **Database:** Supabase (PostgreSQL + pgvector for long-term memory).
- **Backend:** Python (FastAPI).
- **Frontend:** React (Minimal dashboard for auth and Steel "Live View").

## Getting Started
1. Install dependencies: `pip install -r backend/requirements.txt`
2. Set up Temporal: `temporal server start-dev`
3. Configure `.env` (see `env.example`)
4. Run the backend: `python backend/main.py`

