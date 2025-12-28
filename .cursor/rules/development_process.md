# Joint Development Workflow

## Muscle Memory Policy
To help the user (re)learn coding, we follow these rules:

1. **User Responsibilities (Hand-coding):**
   - Temporal Workflow and Activity definitions.
   - Steel browser interaction logic (selectors, navigation).
   - Gemini 3 prompt engineering and tool-calling logic.
   - Core business logic and state transitions.

2. **AI Responsibilities (Tedious Tasks):**
   - Boilerplate setup (FastAPI routes, Pydantic models).
   - Configuration files (Docker, env, requirements.txt).
   - Database migrations and basic CRUD functions.
   - Frontend layout and CSS (unless specified otherwise).

3. **Interaction Pattern:**
   - I (the AI) will provide the code blocks for the "User Responsibilities" and explain the "why" behind them.
   - The User will type/copy-paste these into the editor.
   - I will provide commands to run and test.

## Tech Stack Specifics
- **Python:** Use `poetry` or `pip` (user choice).
- **Style:** Clean, documented, type-hinted code.
- **Testing:** Integration tests for the full HITL loop.

