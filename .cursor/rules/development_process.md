# Joint Development Workflow

## Muscle Memory Policy
To help the user (re)learn coding, we follow these rules:

1. **User Responsibilities (Hand-coding):**
   - Temporal Workflow and Activity definitions.
   - Steel browser interaction logic (selectors, navigation).
   - Supermemory API integration and prompt injection.
   - Gemini 3 planning and self-correction logic.

2. **AI Responsibilities (Tedious Tasks):**
   - Boilerplate setup (Next.js components, FastAPI boilerplate).
   - Configuration files (Docker, env, requirements.txt).
   - Database migrations and basic CRUD functions.
   - CSS and layout adjustments.

3. **Interaction Pattern:**
   - I (the AI) will provide the code blocks and explain the "why".
   - The User will type/copy-paste these into the editor.
   - I will provide commands to run and test.

## Tech Stack Specifics
- **Backend:** FastAPI, Temporal, Supermemory Python SDK.
- **Frontend:** Next.js (App Router), Tailwind CSS, Lucide Icons.
- **Style:** Clean, documented, type-hinted code.
