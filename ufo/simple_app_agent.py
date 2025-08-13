"""
A minimal variant of the AppAgent that retains process association and
core processing logic without relying on the heavy inheritance tree used
in the main project. It exposes a small API so helper scripts can run
an AppAgent in isolation.
"""

from __future__ import annotations

from typing import Optional

from ufo.config.config import Config
from ufo.simple_app_agent_processor import SimpleAppAgentProcessor
from ufo.automator import puppeteer
from ufo.simple_context import SimpleContext
from ufo.simple_app_prompter import SimpleAppPrompter

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
        is_visual: bool = False,
        main_prompt: Optional[str] = None,
        mode: str = "normal",
    ) -> None:
        self.name = f"SimpleAppAgent/{app_root_name}/{process_name}"
        self.process_name = process_name
        self.app_root_name = app_root_name
        self.mode = mode
        self.request = request

        if main_prompt is None:
            main_prompt = configs["APPAGENT_PROMPT"]
        self.prompter = SimpleAppPrompter(main_prompt, is_visual)
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
        return cls(
            process_name,
            app_root_name,
            request,
            is_visual=configs.get("APP_AGENT", {}).get("VISUAL_MODE", False),
            main_prompt=configs.get("APPAGENT_PROMPT"),
            mode=mode,
        )

    def context_provision(self, request: str = "") -> None:
        """Initialize any retrievers based on configuration."""
        _ = request  # kept for API compatibility
        # Simplified agent does not load additional retrievers.

    def message_constructor(
        self,
        dynamic_examples: list[str],
        dynamic_knowledge: list[str],
        image_list: list[str],
        control_info: str,
        plan: list[str],
        request: str,
        subtask: str,
        current_application: str,
        blackboard_prompt: list | str,
        last_success_actions: list,
        include_last_screenshot: bool,
    ) -> list[dict]:
        """Construct the prompt message using :class:`SimpleAppPrompter`."""

        system = self.prompter.system_prompt_construction(dynamic_examples)
        user_content = self.prompter.user_content_construction(
            image_list=image_list,
            control_item=control_info,
            prev_subtask=[],
            prev_plan=plan,
            user_request=request,
            subtask=subtask,
            current_application=current_application,
            host_message=[],
            retrieved_docs="\n".join(dynamic_knowledge),
            last_success_actions=last_success_actions,
            include_last_screenshot=include_last_screenshot,
        )

        if blackboard_prompt:
            user_content = blackboard_prompt + user_content

        return self.prompter.prompt_construction(system, user_content)

    def process(self, context: SimpleContext) -> None:
        """Run one processing step using the standard processor."""
        self.processor = SimpleAppAgentProcessor(agent=self, context=context)
        self.processor.process()
        self.status = self.processor.status
        self.step += 1

    @property
    def is_finished(self) -> bool:
        """Return True if the agent has finished or hit an error."""
        return self.status in (FINISH, ERROR)

