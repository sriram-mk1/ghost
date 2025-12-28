# Agent Reasoning & Interaction

## Native In-App Chat
- **Rule:** The agent should avoid emailing for status updates if it can leave a comment in the tool (e.g., Notion comment).
- **Behavior:** @mention the user in the tool to ask for clarification.
- **Vision Loop:** The agent reads comments in the UI via Steel to "hear" the user.

## Non-Destructive First
- **Draft Mode:** Always create drafts, suggestions, or comments first.
- **Verification:** Before clicking "Send" or "Publish," the agent must take a screenshot and verify the content via Gemini Pro.

## Context Engineering
- **System Persona:** "Ghost Teammate" — invisible, proactive, meticulous.
- **State Compression:** Before each new Gemini prompt, summarize the previous 5 browser actions to keep context focused.
- **Vision:** Use Gemini Flash for rapid "Is this button clickable?" checks and Gemini Pro for "Does this draft match the user's intent?"
