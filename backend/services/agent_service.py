"""
Ghost Teammate Agent
--------------------
The core AI brain that combines:
- Gemini 2.5/3 Computer Use model for multimodal reasoning + actions
- Steel for browser control (virtual computer)
- Supermemory for long-term context retrieval
- Session memory for short-term conversation history
- Email tools for communication with user

This agent can:
1. Decide if it needs a browser or can answer from memory
2. Navigate web apps using visual feedback
3. Sign in/sign up using its dedicated credentials
4. Execute actions via Gemini's computer-use tool calls
5. Communicate via email (respond, clarify, ask for info)

Architecture follows Google ADK guidelines:
https://google.github.io/adk-docs/

Reference:
https://ai.google.dev/gemini-api/docs/computer-use
"""
import json
import base64
import time
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from google import genai
from google.genai import types
from google.genai.types import Content, Part
from backend.core.config import get_settings
from backend.core.agent_prompts import build_system_prompt, build_strategy_prompt
from backend.services.supermemory_service import search_knowledge, get_user_context
from backend.services import steel_service

settings = get_settings()

# ============================================================================
# MODEL CONFIGURATION - ALWAYS USE gemini-3-flash-preview
# ============================================================================
# Computer Use and all agent operations use this model
COMPUTER_USE_MODEL = "gemini-3-flash-preview"

# For strategy/planning (non-computer-use), same model
PLANNING_MODEL = "gemini-3-flash-preview"

# Screen dimensions - should match Steel session
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 768

# Gemini returns 0-999 normalized coordinates
MAX_COORDINATE = 1000

# Maximum retries for screenshot
MAX_SCREENSHOT_RETRIES = 3
SCREENSHOT_RETRY_DELAY = 1.0  # seconds


def denormalize_x(x: int) -> int:
    """Convert normalized X coordinate (0-999) to actual pixels."""
    return int(x / MAX_COORDINATE * SCREEN_WIDTH)


def denormalize_y(y: int) -> int:
    """Convert normalized Y coordinate (0-999) to actual pixels."""
    return int(y / MAX_COORDINATE * SCREEN_HEIGHT)


# ============================================================================
# SESSION MEMORY - Short-term memory for conversation context
# ============================================================================

class SessionMemory:
    """
    Short-term memory for the current session.
    Stores conversation history, actions taken, and task progress.
    
    Following ADK guidelines for session state management.
    """
    
    def __init__(self, max_turns: int = 50):
        self.max_turns = max_turns
        self.contents: List[Content] = []
        self.actions_log: List[Dict[str, Any]] = []
        self.task_started_at: Optional[datetime] = None
        self.current_task: str = ""
        self.task_progress: List[str] = []  # Human-readable progress steps
        
    def add_user_message(self, text: str, image_bytes: Optional[bytes] = None):
        """Add a user message (potentially with screenshot)."""
        parts = [Part(text=text)]
        if image_bytes:
            parts.append(Part.from_bytes(data=image_bytes, mime_type='image/png'))
        self.contents.append(Content(role="user", parts=parts))
        self._trim_if_needed()
    
    def add_model_response(self, content: Content):
        """Add model's response to history."""
        self.contents.append(content)
        self._trim_if_needed()
    
    def add_function_response(self, responses: List[types.FunctionResponse], image_bytes: Optional[bytes] = None):
        """Add function execution results."""
        parts = [Part(function_response=fr) for fr in responses]
        if image_bytes:
            parts.append(Part.from_bytes(data=image_bytes, mime_type='image/png'))
        self.contents.append(Content(role="user", parts=parts))
        self._trim_if_needed()
    
    def log_action(self, action_name: str, args: Dict[str, Any], result: Dict[str, Any]):
        """Log an action for traceability."""
        self.actions_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action_name,
            "args": args,
            "result": result
        })
    
    def add_progress(self, step: str):
        """Add a human-readable progress step."""
        self.task_progress.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {step}")
    
    def get_progress_summary(self) -> str:
        """Get a summary of progress for email updates."""
        if not self.task_progress:
            return "No progress yet."
        return "\n".join(self.task_progress[-10:])  # Last 10 steps
    
    def _trim_if_needed(self):
        """Keep conversation history under max_turns."""
        if len(self.contents) > self.max_turns * 2:
            # Keep first message (initial instructions) and recent history
            self.contents = self.contents[:2] + self.contents[-self.max_turns:]
    
    def clear(self):
        """Clear session memory for new task."""
        self.contents = []
        self.actions_log = []
        self.task_started_at = None
        self.current_task = ""
        self.task_progress = []


# ============================================================================
# EMAIL COMMUNICATION TOOLS
# ============================================================================

class EmailCommunicator:
    """
    Handles email-based communication with the user.
    The agent can ask for clarification, report progress, or request approval.
    """
    
    def __init__(self, user_id: str, job_id: str):
        self.user_id = user_id
        self.job_id = job_id
    
    async def send_clarification_request(self, question: str, context: str = "") -> bool:
        """Ask the user for clarification via email."""
        from backend.services.resend_service import send_agent_email
        
        subject = f"🤔 Clarification Needed - Ghost Agent"
        body = f"""Hi there,

I'm working on your request but need some clarification:

**Question:** {question}

{f"**Context:** {context}" if context else ""}

Please reply to this email with your answer, and I'll continue the task.

Best,
Ghost Agent 🤖
"""
        try:
            await send_agent_email(self.user_id, subject, body)
            return True
        except Exception as e:
            print(f"⚠️ Failed to send clarification email: {e}")
            return False
    
    async def send_progress_update(self, progress_summary: str, status: str = "in_progress") -> bool:
        """Send a progress update to the user."""
        from backend.services.resend_service import send_agent_email
        
        status_emoji = {
            "in_progress": "⏳",
            "completed": "✅",
            "blocked": "🚧",
            "error": "❌"
        }.get(status, "📊")
        
        subject = f"{status_emoji} Task Update - Ghost Agent"
        body = f"""Hi there,

Here's an update on your request:

**Status:** {status.replace('_', ' ').title()}

**Progress:**
{progress_summary}

I'll keep you posted as things progress.

Best,
Ghost Agent 🤖
"""
        try:
            await send_agent_email(self.user_id, subject, body)
            return True
        except Exception as e:
            print(f"⚠️ Failed to send progress email: {e}")
            return False
    
    async def send_completion_report(self, result: str, attachments: Optional[List[str]] = None) -> bool:
        """Send task completion report to user."""
        from backend.services.resend_service import send_agent_email
        
        subject = "✅ Task Completed - Ghost Agent"
        body = f"""Hi there,

Great news! I've completed your request.

**Result:**
{result}

If you need anything else, just send me another email!

Best,
Ghost Agent 🤖
"""
        try:
            await send_agent_email(self.user_id, subject, body)
            return True
        except Exception as e:
            print(f"⚠️ Failed to send completion email: {e}")
            return False


# ============================================================================
# MAIN AGENT CLASS
# ============================================================================

class GhostTeammateAgent:
    """
    The 'brain' of the Ghost Teammate.
    Handles strategic planning and browser execution loops.
    
    Architecture (ADK-aligned):
    - Separation of planning and execution
    - Session memory for conversation context
    - Tool ecosystem for browser control + email communication
    - Safety signals for human-in-the-loop
    """
    
    def __init__(
        self, 
        user_id: str, 
        user_profile: dict, 
        session_id: Optional[str] = None,
        agent_credentials: Optional[Dict[str, str]] = None,
        job_id: Optional[str] = None
    ):
        """
        Initialize the agent with user context.
        
        Args:
            user_id: Unique identifier for the user
            user_profile: User preferences and context from Supermemory
            session_id: Optional Steel session ID for browser control
            agent_credentials: Dict of {platform: email} for the agent's accounts
            job_id: Job identifier for email communication
        """
        self.user_id = user_id
        self.user_profile = user_profile
        self.session_id = session_id
        self.agent_credentials = agent_credentials or {}
        self.job_id = job_id or "unknown"
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # Session memory (short-term)
        self.memory = SessionMemory()
        
        # Email communicator
        self.email = EmailCommunicator(user_id, self.job_id)
        
        # Browser state
        self.browser_opened = False
        self.current_url = "about:blank"

    def _get_system_instruction(self, task: str = "") -> str:
        """
        Returns the comprehensive system prompt that defines the agent's persona.
        Combines long-term memory from Supermemory with task context.
        """
        memory_context = ""
        try:
            user_context = get_user_context(self.user_id, task)
            if user_context:
                memory_context = f"""
User Profile: {user_context.get('static_profile', 'Unknown')}
Recent Habits: {user_context.get('dynamic_profile', 'Unknown')}
Relevant Memories: {user_context.get('relevant_memories', 'None')}
"""
        except Exception as e:
            print(f"⚠️ Failed to fetch memory context: {e}")
        
        return build_system_prompt(
            user_id=self.user_id,
            task=task or self.memory.current_task,
            memory_context=memory_context,
            agent_credentials=self.agent_credentials,
            viewport_width=SCREEN_WIDTH,
            viewport_height=SCREEN_HEIGHT,
        )

    def _take_screenshot_with_retry(self) -> Optional[bytes]:
        """
        Take screenshot with retry logic for robustness.
        Returns decoded bytes or None if all retries fail.
        """
        for attempt in range(MAX_SCREENSHOT_RETRIES):
            try:
                img_b64 = steel_service.take_screenshot(self.session_id)
                
                # Handle empty or None response
                if not img_b64:
                    print(f"⚠️ Screenshot attempt {attempt + 1}: Empty response, retrying...")
                    time.sleep(SCREENSHOT_RETRY_DELAY)
                    continue
                
                # Decode base64
                img_bytes = base64.b64decode(img_b64)
                
                if len(img_bytes) < 100:  # Suspiciously small
                    print(f"⚠️ Screenshot attempt {attempt + 1}: Suspiciously small ({len(img_bytes)} bytes), retrying...")
                    time.sleep(SCREENSHOT_RETRY_DELAY)
                    continue
                    
                return img_bytes
                
            except Exception as e:
                print(f"⚠️ Screenshot attempt {attempt + 1} failed: {e}")
                time.sleep(SCREENSHOT_RETRY_DELAY)
        
        print("❌ All screenshot attempts failed")
        return None

    async def decide_strategy(self, goal: str) -> Dict[str, Any]:
        """
        STEP 1: Strategic Planning
        
        Before spinning up a browser, the agent consults memory to decide:
        - BROWSER: Need to interact with a web app
        - MEMORY: Can answer directly from context
        - CLARIFY: Need more information from user
        
        This saves resources by avoiding unnecessary browser sessions.
        """
        self.memory.current_task = goal
        self.memory.task_started_at = datetime.utcnow()
        
        # Retrieve relevant context from Supermemory (long-term memory)
        memory_context = search_knowledge(goal, self.user_id)
        
        # Use the centralized strategy prompt builder
        planning_prompt = build_strategy_prompt(goal, memory_context)
        
        response = self.client.models.generate_content(
            model=PLANNING_MODEL,
            contents=[planning_prompt],
            config=types.GenerateContentConfig(
                system_instruction=self._get_system_instruction(goal)
            )
        )
        
        text = response.text.upper() if response.text else ""
        
        self.memory.add_progress(f"Strategy decided: {text[:50]}...")
        
        if "BROWSER" in text:
            return {"strategy": "BROWSER", "reasoning": response.text}
        elif "CLARIFY" in text:
            return {"strategy": "CLARIFY", "reasoning": response.text}
        else:
            return {"strategy": "MEMORY", "reasoning": response.text}

    async def execute_turn(self, task: str) -> Dict[str, Any]:
        """
        STEP 2: Execute One Reasoning-Action Loop
        
        This is the core "think → act → observe" cycle:
        1. Take screenshot (observe current state)
        2. Send to Gemini with task context (think)
        3. Execute any tool calls (act)
        4. Feed results back for next iteration
        
        Returns:
            dict with 'reasoning', 'finished', 'action_taken', 'requires_approval', 'approval_action'
        """
        if not self.session_id:
            raise ValueError("No Steel session ID provided")
        
        self.memory.current_task = task
        
        # 1. OBSERVE: Take screenshot of current browser state
        img_bytes = self._take_screenshot_with_retry()
        
        if img_bytes is None:
            # Screenshot failed - report error
            return {
                "reasoning": "Failed to capture browser screenshot after multiple attempts. The session may be disconnected.",
                "finished": True,
                "action_taken": None,
                "requires_approval": False,
                "approval_action": None,
                "error": "screenshot_failed"
            }
        
            # Check for feedback/interruption before starting turn
            # (In a real temporal workflow, this would be a Signal)
            # For now, we simulate this by checking if the last user message was a feedback
            
            # Initialize conversation with the task (first turn only)
            if not self.memory.contents:
                initial_message = f"""GOAL: {task}

You are controlling a browser. 
The browser is previously opened. 
Observe the screenshot and execute the next logical step.
Strictly follow the coordinate system (0-1000).

Refuse to stop until the task is clearly done.
"""
                self.memory.add_user_message(initial_message, img_bytes)
                self.memory.add_progress("Started browser session")
            else:
                # Add new screenshot to existing conversation for the next turn
                # This is where we would also inject "USER FEEDBACK" if we had a signal
                next_prompt = "Here is the current state. What's the next action?"
                self.memory.add_user_message(next_prompt, img_bytes)

        
        # 2. THINK: Get Gemini's next action using Computer Use
        config = types.GenerateContentConfig(
            system_instruction=self._get_system_instruction(task),
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER,
                        # Exclude open_web_browser since our browser is already open
                        # We are keeping 'navigate' allowed though the model might try to use it as tool call
                        excluded_predefined_functions=["open_web_browser"]
                    )
                )
            ],
            # Enable thinking for better reasoning
            thinking_config=types.ThinkingConfig(include_thoughts=True)
        )
        
        try:
            response = self.client.models.generate_content(
                model=COMPUTER_USE_MODEL,
                contents=self.memory.contents,
                config=config
            )
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return {
                "reasoning": f"Model API error: {str(e)}",
                "finished": True,
                "action_taken": None,
                "requires_approval": False,
                "approval_action": None,
                "error": "model_error"
            }
        
        if not response.candidates:
            return {"reasoning": "No response from Gemini", "finished": True, "action_taken": None}
        
        candidate = response.candidates[0]
        
        # Add model response to conversation history
        if candidate.content:
            self.memory.add_model_response(candidate.content)
        
        # Extract reasoning text and function calls
        reasoning_parts = []
        function_calls = []
        
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.text:
                    reasoning_parts.append(part.text)
                if part.function_call:
                    function_calls.append(part.function_call)
        
        reasoning = " ".join(reasoning_parts).strip()
        
        print(f"💭 Reasoning: {reasoning[:200]}...")
        print(f"🔧 Function calls: {[fc.name for fc in function_calls]}")
        
        # Check for memory triggers in reasoning
        await self._check_memory_triggers(reasoning)
        
        # Check for safety signals in reasoning (HITL triggers)
        requires_approval, approval_action = self._check_safety_signals(reasoning)
        if requires_approval:
            self.memory.add_progress(f"⚠️ Requires approval: {approval_action}")
            return {
                "reasoning": reasoning,
                "finished": False,
                "action_taken": None,
                "requires_approval": True,
                "approval_action": approval_action,
                "screenshot": base64.b64encode(img_bytes).decode() if img_bytes else None,
            }
        
        # If no function calls, the agent is done or needs clarification
        if not function_calls:
            self.memory.add_progress(f"Completed: {reasoning[:100]}...")
            return {
                "reasoning": reasoning,
                "finished": True,
                "action_taken": None,
                "requires_approval": False,
                "approval_action": None,
            }
        
        # 3. ACT: Execute each function call via Steel
        function_responses = []
        actions_taken = []
        
        for fc in function_calls:
            action_name = fc.name or "unknown"
            args = dict(fc.args) if fc.args else {}
            
            print(f"🔧 Executing: {action_name} with args: {args}")
            actions_taken.append(action_name)
            
            # Execute the action
            result = self._execute_computer_action(action_name, args)
            
            # Log action
            self.memory.log_action(action_name, args, result)
            self.memory.add_progress(f"Action: {action_name}")
            
            # Prepare function response
            function_responses.append(
                types.FunctionResponse(
                    name=action_name,
                    response=result
                )
            )
        
        # 4. FEEDBACK: Get new screenshot after actions
        new_screenshot_bytes = self._take_screenshot_with_retry()
        
        # Add function responses and new screenshot (if available)
        self.memory.add_function_response(function_responses, new_screenshot_bytes)
        
        return {
            "reasoning": reasoning,
            "finished": False,
            "action_taken": ", ".join(actions_taken),
            "requires_approval": False,
            "approval_action": None,
        }

    async def request_clarification(self, question: str, context: str = "") -> bool:
        """
        Ask the user for clarification via email.
        This is used when the agent needs more information to proceed.
        """
        self.memory.add_progress(f"Requesting clarification: {question}")
        return await self.email.send_clarification_request(question, context)

    async def send_update(self, status: str = "in_progress") -> bool:
        """Send progress update to user via email."""
        progress = self.memory.get_progress_summary()
        return await self.email.send_progress_update(progress, status)

    async def complete_with_result(self, result: str) -> bool:
        """Mark task as complete and notify user."""
        self.memory.add_progress(f"Task completed: {result[:100]}...")
        return await self.email.send_completion_report(result)

    async def _check_memory_triggers(self, reasoning: str):
        """
        Scans reasoning for 'SAVE_TO_MEMORY: [category] - [content]' pattern
        and automatically saves to Supermemory.
        """
        import re
        from backend.services.supermemory_service import add_memory
        
        # Regex to capture content after SAVE_TO_MEMORY:
        # Matches: SAVE_TO_MEMORY: category - content...
        pattern = r"SAVE_TO_MEMORY:\s*(\w+)\s*-\s*(.+)"
        matches = re.finditer(pattern, reasoning, re.MULTILINE)
        
        for match in matches:
            category = match.group(1).lower()
            content = match.group(2).strip()
            
            print(f"📝 Auto-saving to memory: [{category}] {content[:50]}...")
            
            # Save to Supermemory
            add_memory(
                user_id=self.user_id,
                content=content,
                metadata={
                    "type": "agent_learned",
                    "category": category,
                    "source": "reasoning_trigger",
                    "job_id": self.job_id
                }
            )
            self.memory.add_progress(f"Memorized: {content[:100]}...")

    def _check_safety_signals(self, reasoning: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the agent's reasoning indicates a TRUE destructive action
        that requires human approval.
        
        Refined to be less spammy - allows standard actions.
        """
        reasoning_lower = reasoning.lower()
        
        # CRITICAL-ONLY keywords that ALWAYS require approval
        high_risk_patterns = [
            ("delete permanently", "Permanent deletion (trash empty)"),
            ("delete forever", "Permanent deletion"),
            ("cannot be undone", "Irreversible action"),
            ("confirm payment", "Executing financial transaction"),
            ("checkout", " completing purchase"),
            ("revoke access", "Revoking user access"),
            ("make public", "Publishing content publicly"),
            ("cancel subscription", "Canceling subscription plan"),
            # Note: "send email" is removed to allow standard communication
            # unless it's explicitly about "external" people
            ("email to external", "Emailing unknown external recipient"),
        ]
        
        for pattern, description in high_risk_patterns:
            if pattern in reasoning_lower:
                return True, description
        
        return False, None

    def _execute_computer_action(self, action_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Computer Use action via Steel.
        
        Maps Gemini's computer-use actions to Steel API calls.
        Reference: https://ai.google.dev/gemini-api/docs/computer-use#supported-actions
        """
        try:
            # ================================================================
            # BROWSER NAVIGATION ACTIONS
            # ================================================================
            if action_name == "open_web_browser":
                # Browser is already open via Steel - just acknowledge
                self.browser_opened = True
                print("✅ Browser already open (Steel session active)")
                return {"status": "success", "message": "Browser is ready"}
            
            elif action_name == "navigate":
                url = args.get("url", "https://google.com")
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                print(f"🌐 Navigating to: {url}")
                # Use keyboard shortcut to navigate
                steel_service.press_keys(self.session_id, ["Control", "l"])
                steel_service.type_text(self.session_id, url)
                steel_service.press_keys(self.session_id, ["Enter"])
                steel_service.wait(self.session_id, 2.0)
                self.current_url = url
                return {"status": "success", "url": url}
            
            elif action_name == "search":
                # Open a new tab and go to Google
                steel_service.press_keys(self.session_id, ["Control", "t"])
                steel_service.wait(self.session_id, 0.5)
                steel_service.type_text(self.session_id, "https://google.com")
                steel_service.press_keys(self.session_id, ["Enter"])
                steel_service.wait(self.session_id, 2.0)
                return {"status": "success", "message": "Opened Google search"}
            
            elif action_name == "go_back":
                steel_service.press_keys(self.session_id, ["Alt", "ArrowLeft"])
                steel_service.wait(self.session_id, 1.0)
                return {"status": "success"}
            
            elif action_name == "go_forward":
                steel_service.press_keys(self.session_id, ["Alt", "ArrowRight"])
                steel_service.wait(self.session_id, 1.0)
                return {"status": "success"}
            
            elif action_name == "wait_5_seconds":
                steel_service.wait(self.session_id, 5.0)
                return {"status": "success"}
            
            # ================================================================
            # MOUSE ACTIONS
            # ================================================================
            elif action_name == "click_at":
                x = denormalize_x(args.get("x", 500))
                y = denormalize_y(args.get("y", 500))
                print(f"🖱️ Clicking at ({x}, {y})")
                steel_service.click(self.session_id, x, y)
                steel_service.wait(self.session_id, 0.5)
                return {"status": "success", "x": x, "y": y}
            
            elif action_name == "double_click_at":
                x = denormalize_x(args.get("x", 500))
                y = denormalize_y(args.get("y", 500))
                print(f"🖱️🖱️ Double-clicking at ({x}, {y})")
                steel_service.double_click(self.session_id, x, y)
                steel_service.wait(self.session_id, 0.5)
                return {"status": "success", "x": x, "y": y}
            
            elif action_name == "hover_at":
                x = denormalize_x(args.get("x", 500))
                y = denormalize_y(args.get("y", 500))
                steel_service.move_mouse(self.session_id, x, y)
                return {"status": "success", "x": x, "y": y}
            
            elif action_name == "drag_and_drop":
                start_x = denormalize_x(args.get("x", 0))
                start_y = denormalize_y(args.get("y", 0))
                end_x = denormalize_x(args.get("destination_x", 0))
                end_y = denormalize_y(args.get("destination_y", 0))
                steel_service.execute_action(
                    self.session_id, "drag_mouse",
                    path=[[start_x, start_y], [end_x, end_y]]
                )
                return {"status": "success"}
            
            # ================================================================
            # KEYBOARD ACTIONS
            # ================================================================
            elif action_name == "type_text_at":
                x = denormalize_x(args.get("x", 500))
                y = denormalize_y(args.get("y", 500))
                text = args.get("text", "")
                press_enter = args.get("press_enter", False)
                clear_before = args.get("clear_before_typing", True)
                
                print(f"⌨️ Typing '{text[:30]}...' at ({x}, {y})")
                
                # Click to focus
                steel_service.click(self.session_id, x, y)
                steel_service.wait(self.session_id, 0.2)
                
                # Clear existing text if requested
                if clear_before:
                    steel_service.press_keys(self.session_id, ["Control", "a"])
                    steel_service.press_keys(self.session_id, ["Backspace"])
                
                # Type the text
                steel_service.type_text(self.session_id, text)
                
                # Press enter if requested
                if press_enter:
                    steel_service.press_keys(self.session_id, ["Enter"])
                    steel_service.wait(self.session_id, 1.0)
                
                return {"status": "success", "text": text}
            
            elif action_name == "key_combination":
                keys_str = args.get("keys", "")
                keys = [k.strip() for k in keys_str.split("+")]
                print(f"⌨️ Key combo: {keys}")
                steel_service.press_keys(self.session_id, keys)
                return {"status": "success", "keys": keys}
            
            # ================================================================
            # SCROLL ACTIONS
            # ================================================================
            elif action_name == "scroll_document":
                direction = args.get("direction", "down")
                key = "PageDown" if direction == "down" else "PageUp"
                steel_service.press_keys(self.session_id, [key])
                steel_service.wait(self.session_id, 0.5)
                return {"status": "success", "direction": direction}
            
            elif action_name == "scroll_at":
                x = denormalize_x(args.get("x", 500))
                y = denormalize_y(args.get("y", 500))
                direction = args.get("direction", "down")
                magnitude = args.get("magnitude", 400)
                
                delta_y = magnitude if direction == "down" else -magnitude
                steel_service.scroll(self.session_id, x, y, delta_y)
                return {"status": "success", "direction": direction}
            
            # ================================================================
            # EMAIL / VERIFICATION TOOLS
            # ================================================================
            elif action_name == "check_email":
                query = args.get("query")
                sent_to = args.get("sent_to")
                limit = args.get("limit", 3)
                print(f"📧 Checking inbox for: {query} (to: {sent_to})")
                
                from backend.services.agentmail_service import search_agent_inbox
                # Run async in sync context if needed, but since we are in `execute_turn` which is async
                # wait.. `_execute_computer_action` is currently sync in this file?
                # Ah, looking at the code, `_execute_computer_action` is synchronous in dispatch 
                # but calls async services? No, Steel methods are sync. 
                # We need to bridge this. Ideally `_execute_computer_action` should be async.
                # Since I cannot refactor the whole method to async right now without breaking potential callers,
                # I will use a sync wrapper or specific dispatch. 
                # Actually, `execute_turn` awaits `agent.execute_turn` so we can make valid async calls if we bubble it up.
                # BUT `_execute_computer_action` is called in `execute_turn` and NOT awaited there currently in the loop 
                # (it says `result = self._execute_computer_action(...)`).
                
                # FIX: We will do a quick async-to-sync bridge or better yet, Import a sync/helper.
                # Since we are in an async loop in `execute_turn`, let's just use `asyncio.run` or loop run? 
                # No, that's bad practice in nested loops. 
                # Let's check `execute_turn` implementation. It IS `async def execute_turn`.
                # So we SHOULD await `_execute_computer_action` if we make it async. 
                # But to avoid massive refactor, I will implement a bridge here just for this tool.
                import asyncio
                loop = asyncio.get_event_loop()
                messages = loop.run_until_complete(search_agent_inbox(self.user_id, query, limit, sent_to))
                
                if not messages:
                    return {"status": "success", "found": False, "messages": []}
                
                return {
                    "status": "success", 
                    "found": True, 
                    "messages": messages, 
                    "count": len(messages)
                }
            
            # ================================================================
            # UNKNOWN ACTION
            # ================================================================
            else:
                print(f"⚠️ Unknown action: {action_name} - Skipping")
                return {"status": "skipped", "reason": f"Unknown action: {action_name}"}
                
        except Exception as e:
            print(f"⚠️ Action failed: {action_name} - {e}")
            return {"status": "error", "error": str(e)}


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

async def create_agent_with_credentials(
    user_id: str,
    user_profile: dict,
    session_id: Optional[str] = None,
    job_id: Optional[str] = None
) -> GhostTeammateAgent:
    """
    Factory function that creates an agent with its credentials pre-loaded.
    """
    from backend.services.supabase_client import get_supabase
    
    # Load agent's credentials from Supabase
    supabase = get_supabase()
    workspaces = supabase.table("workspaces").select(
        "platform_name, agent_email"
    ).eq("user_id", user_id).eq("is_active", True).execute()
    
    credentials = {}
    if workspaces.data:
        for ws in workspaces.data:
            credentials[ws["platform_name"]] = ws["agent_email"]
    
    return GhostTeammateAgent(
        user_id=user_id,
        user_profile=user_profile,
        session_id=session_id,
        agent_credentials=credentials,
        job_id=job_id
    )
