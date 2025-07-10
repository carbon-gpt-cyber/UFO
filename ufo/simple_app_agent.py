"""
A minimal variant of the AppAgent that retains process association and
core processing logic without relying on the heavy inheritance tree used
in the main project. It exposes a small API so helper scripts can run
an AppAgent in isolation.
"""

from __future__ import annotations

from typing import Optional

from ufo.config.config import Config
from ufo.agents.processors.app_agent_action_seq_processor import (
    AppAgentActionSequenceProcessor,
)
from ufo.simple_app_agent_processor import SimpleAppAgentProcessor
from ufo.automator import puppeteer
from ufo.simple_context import SimpleContext
from ufo.prompter.agent_prompter import AppAgentPrompter

configs = Config.get_instance().config_data

# Basic status strings used by the simplified agent
FINISH = "FINISH"
ERROR = "ERROR"
CONTINUE = "CONTINUE"

class SimpleAppAgent:
    """A lightweight AppAgent with only the essentials."""

    def __init__(
        self,
        process_name: str,
        app_root_name: str,
        request: str = "",
        is_visual: Optional[bool] = None,
        main_prompt: Optional[str] = None,
        example_prompt: Optional[str] = None,
        api_prompt: Optional[str] = None,
        mode: str = "normal",
    ) -> None:
        self.name = f"SimpleAppAgent/{app_root_name}/{process_name}"
        self.process_name = process_name
        self.app_root_name = app_root_name
        self.mode = mode
        self.request = request

        if is_visual is None:
            is_visual = configs["APP_AGENT"]["VISUAL_MODE"]
        if main_prompt is None:
            main_prompt = configs["APPAGENT_PROMPT"]
        if example_prompt is None:
            example_prompt = (
                configs["APPAGENT_EXAMPLE_PROMPT_AS"]
                if configs.get("ACTION_SEQUENCE", False)
                else configs["APPAGENT_EXAMPLE_PROMPT"]
            )
        if api_prompt is None:
            api_prompt = configs["API_PROMPT"]

        self.prompter = AppAgentPrompter(
            is_visual, main_prompt, example_prompt, api_prompt, app_root_name
        )
        self.Puppeteer = puppeteer.AppPuppeteer(process_name, app_root_name)

        self.status = CONTINUE
        self.processor: Optional[SimpleAppAgentProcessor] = None
        self.step = 0


        if configs.get("USE_APIS", False):
            self.Puppeteer.receiver_manager.create_api_receiver(
                app_root_name, process_name
            )

        self.context_provision(request)

    @classmethod
    def from_config(
        cls, process_name: str, app_root_name: str, request: str = "", mode: str = "normal"
    ) -> "SimpleAppAgent":
        """Create the agent using values from the global configuration."""
        return cls(process_name, app_root_name, request, mode=mode)

    def context_provision(self, request: str = "") -> None:
        """Initialize any retrievers based on configuration."""
        _ = request  # kept for API compatibility
        # Simplified agent does not load additional retrievers.

    def process(self, context: SimpleContext) -> None:
        """Run one processing step using the standard processor."""
        if configs.get("ACTION_SEQUENCE", False):
            self.processor = AppAgentActionSequenceProcessor(
                agent=self, context=context
            )
        else:
            self.processor = SimpleAppAgentProcessor(
                agent=self, context=context
            )
        self.processor.process()
        self.status = self.processor.status
        self.step += 1

    @property
    def is_finished(self) -> bool:
        """Return True if the agent has finished or hit an error."""
        return self.status in (FINISH, ERROR)

