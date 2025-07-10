from __future__ import annotations

from typing import Any, Dict, List

from ufo.prompter.basic import BasicPrompter


class SimpleAppPrompter:
    """Load a single prompt template and fill it for :class:`SimpleAppAgent`."""

    def __init__(self, prompt_template: str, is_visual: bool = False) -> None:
        self.is_visual = is_visual
        self.prompt_template = BasicPrompter.load_prompt_template(
            prompt_template, is_visual
        )

    # ------------------------------------------------------------------
    def system_prompt_construction(self, examples: List[str] = []) -> str:
        key = "system"
        if not self.is_visual:
            key += "_nonvisual"
        system = self.prompt_template.get(key, "")
        if examples:
            examples_prompt = "\n".join(examples)
            system = system.format(examples=examples_prompt)
        return system

    def user_prompt_construction(
        self,
        control_item: str,
        prev_subtask: List[Dict[str, str]],
        prev_plan: List[str],
        user_request: str,
        subtask: str,
        current_application: str,
        host_message: List[str],
        retrieved_docs: str = "",
        last_success_actions: List[Dict[str, Any]] | None = None,
    ) -> str:
        if last_success_actions is None:
            last_success_actions = []
        template = self.prompt_template.get("user", "")
        return template.format(
            control_item=control_item,
            prev_subtask=prev_subtask,
            prev_plan=prev_plan,
            user_request=user_request,
            subtask=subtask,
            current_application=current_application,
            host_message=host_message,
            retrieved_docs=retrieved_docs,
            last_success_actions=last_success_actions,
        )

    def user_content_construction(
        self,
        image_list: List[str],
        control_item: str,
        prev_subtask: List[Dict[str, str]],
        prev_plan: List[str],
        user_request: str,
        subtask: str,
        current_application: str,
        host_message: List[str],
        retrieved_docs: str = "",
        last_success_actions: List[Dict[str, Any]] | None = None,
        include_last_screenshot: bool = True,
    ) -> List[Dict[str, str]]:
        _ = image_list, include_last_screenshot  # unused in simple mode
        user_text = self.user_prompt_construction(
            control_item=control_item,
            prev_subtask=prev_subtask,
            prev_plan=prev_plan,
            user_request=user_request,
            subtask=subtask,
            current_application=current_application,
            host_message=host_message,
            retrieved_docs=retrieved_docs,
            last_success_actions=last_success_actions or [],
        )
        return [{"type": "text", "text": user_text}]

    # ------------------------------------------------------------------
    @staticmethod
    def prompt_construction(
        system_prompt: str, user_content: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        system_message = {"role": "system", "content": system_prompt}
        user_message = {"role": "user", "content": user_content}
        return [system_message, user_message]
