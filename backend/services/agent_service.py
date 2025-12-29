import os
import json
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from google import genai
from google.genai import types
from google.genai.types import (
    Content,
    Part,
    FunctionCall,
    FunctionResponse,
    Candidate,
    FinishReason,
    Tool,
    GenerateContentConfig,
)
from backend.core.config import get_settings
from backend.services.steel_service import steel_client

settings = get_settings()

MODEL = "gemini-2.5-computer-use-preview-10-2025"
MAX_COORDINATE = 1000

def format_today() -> str:
    return datetime.now().strftime("%A, %B %d, %Y")

BROWSER_SYSTEM_PROMPT = f"""<BROWSER_ENV>
  - You control a headful Chromium browser running in a VM with internet access.
  - Chromium is already open; interact only through computer use actions (mouse, keyboard, scroll, screenshots).
  - Today's date is {format_today()}.
  </BROWSER_ENV>
  
  <BROWSER_CONTROL>
  - When viewing pages, zoom out or scroll so all relevant content is visible.
  - When typing into any input:
    * Clear it first with Ctrl+A, then Delete.
    * After submitting (pressing Enter or clicking a button), wait for the page to load.
  - Computer tool calls are slow; batch related actions into a single call whenever possible.
  - You may act on the user's behalf on sites where they are already authenticated.
  - Assume any required authentication/Auth Contexts are already configured before the task starts.
  </BROWSER_CONTROL>
  
  <TASK_EXECUTION>
  - You receive exactly one natural-language task and no further user feedback.
  - Do not ask the user clarifying questions; instead, make reasonable assumptions and proceed.
  - For complex tasks, quickly plan a short, ordered sequence of steps before acting.
  - Prefer minimal, high-signal actions that move directly toward the goal.
  </TASK_EXECUTION>"""

class GhostAgent:
    """
    The Ghost Teammate's 'Brain'. 
    Integrates Gemini 3 Computer Use with Steel Browser sessions.
    """
    def __init__(self, session_id: str, user_profile: Optional[dict] = None):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.session_id = session_id
        self.user_profile = user_profile or {}
        self.contents: List[Content] = []
        
        # Default viewport for Steel sessions
        self.viewport_width = 1280
        self.viewport_height = 768

        self.tools: List[Tool] = [
            Tool(
                computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_BROWSER,
                )
            )
        ]
        self.config = GenerateContentConfig(tools=self.tools)

    def _denormalize_x(self, x: int) -> int:
        return int(x / MAX_COORDINATE * self.viewport_width)

    def _denormalize_y(self, y: int) -> int:
        return int(y / MAX_COORDINATE * self.viewport_height)

    async def execute_step(self, task: str) -> str:
        """
        Executes a single step of reasoning and action.
        Returns the agent's reasoning/final response.
        """
        if not self.contents:
            # Initialize with system prompt and task
            self.contents = [
                Content(
                    role="user",
                    parts=[
                        Part(text=BROWSER_SYSTEM_PROMPT),
                        Part(text=f"User Context: {json.dumps(self.user_profile)}"),
                        Part(text=f"Task: {task}")
                    ],
                )
            ]

        # 1. Generate reasoning and action from Gemini
        response = self.client.models.generate_content(
            model=MODEL,
            contents=self.contents,
            config=self.config,
        )

        if not response.candidates:
            return "No response from Gemini."

        candidate = response.candidates[0]
        if candidate.content:
            self.contents.append(candidate.content)

        reasoning = self._extract_text(candidate)
        function_calls = self._extract_function_calls(candidate)

        if not function_calls:
            return reasoning or "Task complete."

        # 2. Execute actions via Steel
        results = []
        for fc in function_calls:
            result = await self._execute_computer_action(fc)
            results.append(result)

        # 3. Feed results back to Gemini for the next step
        function_response_parts = self._build_function_response_parts(function_calls, results)
        self.contents.append(Content(role="user", parts=function_response_parts))
        
        return reasoning

    async def _execute_computer_action(self, function_call: FunctionCall) -> Tuple[str, str]:
        """Maps Gemini computer use calls to Steel browser actions."""
        name = function_call.name or ""
        args: Dict[str, Any] = function_call.args or {}

        # Use the Steel Computer API to perform actions
        # This is a high-level wrapper around the Steel /sessions/{id}/computer endpoint
        resp = await steel_client.sessions.computer(
            self.session_id,
            action=self._map_action(name),
            **self._map_args(name, args)
        )
        
        img = getattr(resp, "base64_image", None)
        url = getattr(resp, "url", "about:blank")
        return img, url

    def _map_action(self, name: str) -> str:
        mapping = {
            "click_at": "click_mouse",
            "hover_at": "move_mouse",
            "type_text_at": "type_text",
            "scroll_at": "scroll",
            "open_web_browser": "take_screenshot", # Initialize
        }
        return mapping.get(name, "take_screenshot")

    def _map_args(self, name: str, args: dict) -> dict:
        mapped = {"screenshot": True}
        if "x" in args and "y" in args:
            mapped["coordinates"] = [self._denormalize_x(args["x"]), self._denormalize_y(args["y"])]
        if name == "type_text_at":
            mapped["text"] = args.get("text", "")
        if name == "scroll_at":
            direction = args.get("direction", "down")
            magnitude = self._denormalize_y(args.get("magnitude", 800))
            if direction == "down": mapped["delta_y"] = magnitude
            elif direction == "up": mapped["delta_y"] = -magnitude
        return mapped

    def _extract_text(self, candidate: Candidate) -> str:
        if not candidate.content or not candidate.content.parts:
            return ""
        return " ".join([p.text for p in candidate.content.parts if p.text]).strip()

    def _extract_function_calls(self, candidate: Candidate) -> List[FunctionCall]:
        if not candidate.content or not candidate.content.parts:
            return []
        return [p.function_call for p in candidate.content.parts if p.function_call]

    def _build_function_response_parts(self, function_calls: List[FunctionCall], results: List[Tuple[str, str]]) -> List[Part]:
        parts = []
        for i, fc in enumerate(function_calls):
            img, url = results[i]
            parts.append(Part(function_response=FunctionResponse(name=fc.name, response={"url": url})))
            parts.append(Part(inline_data=types.Blob(mime_type="image/png", data=img)))
        return parts

