"""A simplified processor for `SimpleAppAgent` with minimal
functionality. It avoids inheritance and heavy decorators used in the
original processor while retaining the core ground-decide-act loop."""

from __future__ import annotations

from typing import Any, List

from ufo import utils
from ufo.config.config import Config
from ufo.agents.processors.actions import ActionSequence, OneStepAction
from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.simple_context import (
    SimpleContext,
    APPLICATION_WINDOW,
    LOG_PATH,
    SUBTASK,
    REQUEST,
    LOGGER,
)

configs = Config.get_instance().config_data

if configs is not None:
    CONTROL_BACKEND = configs.get("CONTROL_BACKEND", ["uia"])
    BACKEND = "win32" if "win32" in CONTROL_BACKEND else "uia"


class ControlInfoRecorder:
    """Record information about detected controls."""

    recording_fields: List[str] = [
        "control_text",
        "control_type" if BACKEND == "uia" else "control_class",
        "control_rect",
        "source",
    ]

    def __init__(self) -> None:
        self.merged_controls_info: List[dict] = []


class SimpleAppAgentProcessor:
    """Minimal processor that drives a :class:`SimpleAppAgent`."""

    def __init__(
        self,
        agent: "SimpleAppAgent",
        context: SimpleContext,
    ) -> None:
        self.agent = agent
        self.context = context
        self.control_inspector = ControlInspectorFacade(BACKEND)
        self.control_recorder = ControlInfoRecorder()
        self.status = "CONTINUE"
        self._annotation_dict: dict[str, Any] = {}
        self._operation = ""
        self._args: dict[str, Any] = {}
        self._response_json: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------
    @property
    def application_window(self):
        return self.context.get(APPLICATION_WINDOW)

    @property
    def log_path(self) -> str:
        return self.context.get(LOG_PATH, "")

    @property
    def subtask(self) -> str:
        return self.context.get(SUBTASK, "")

    @property
    def request(self) -> str:
        return self.context.get(REQUEST, self.subtask)

    # ------------------------------------------------------------------
    def print_step_info(self) -> None:
        step = getattr(self.agent, "step", 0) + 1
        utils.print_with_color(
            f"Step {step}, AppAgent: Completing the subtask [{self.subtask}] on application [{self.agent.process_name}].",
            "magenta",
        )

    def get_control_info(self) -> None:
        control_list = self.control_inspector.find_control_elements_in_descendants(
            self.application_window,
            control_type_list=configs.get("CONTROL_LIST", []),
            class_name_list=configs.get("CONTROL_LIST", []),
        )
        self._annotation_dict = {
            str(i + 1): ctl for i, ctl in enumerate(control_list)
        }
        self.control_recorder.merged_controls_info = self.control_inspector.get_control_info_list_of_dict(
            self._annotation_dict, ControlInfoRecorder.recording_fields
        )

    def build_prompt(self) -> None:
        experience, demonstration = self.agent.demonstration_prompt_helper(request=self.subtask)
        retrieved = experience + demonstration

        offline_docs, online_docs = self.agent.external_knowledge_prompt_helper(
            self.subtask,
            configs.get("RAG_OFFLINE_DOCS_RETRIEVED_TOPK", 0),
            configs.get("RAG_ONLINE_RETRIEVED_TOPK", 0),
        )
        external_knowledge = offline_docs + online_docs

        image_list: list[str] = []

        self.prompt_message = self.agent.message_constructor(
            dynamic_examples=retrieved,
            dynamic_knowledge=external_knowledge,
            image_list=image_list,
            control_info=str(self.control_recorder.merged_controls_info),
            plan=[],
            request=self.request,
            subtask=self.subtask,
            current_application=self.agent.process_name,
            blackboard_prompt="",
            last_success_actions=[],
            include_last_screenshot=False,
        )

    def get_response(self) -> None:
        response_str, cost = self.agent.get_response(
            self.prompt_message, self.agent.name, False, configs=configs
        )
        self._response_json = self.agent.response_to_dict(response_str)
        self.cost = cost

    def parse_response(self) -> None:
        self._operation = self._response_json.get("Function", "")
        self._args = utils.revise_line_breaks(self._response_json.get("Args", ""))
        self.control_label = self._response_json.get("ControlLabel", "")
        self.control_text = self._response_json.get("ControlText", "")
        self.plan = self._response_json.get("Plan", [])
        self.status = self._response_json.get("Status", "")
        if not self.status and self._operation.lower() == "finish":
            self.status = "FINISH"
        self.agent.print_response(self._response_json, print_action=True)

    def execute_action(self) -> None:
        control = self._annotation_dict.get(self.control_label)
        if control:
            self.agent.Puppeteer.receiver_manager.create_ui_control_receiver(
                control, self.application_window
            )
        action = OneStepAction(
            function=self._operation,
            args=self._args,
            control_label=self.control_label,
            control_text=self.control_text,
            after_status=self.status,
        )
        seq = ActionSequence(actions=[action])
        seq.execute_all(
            puppeteer=self.agent.Puppeteer,
            control_dict=self._annotation_dict,
            application_window=self.application_window,
        )
        self.actions = seq

    # ------------------------------------------------------------------
    def process(self) -> None:
        try:
            self.print_step_info()
            self.get_control_info()
            self.build_prompt()
            self.get_response()
            self.parse_response()
            self.execute_action()
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.status = "ERROR"
            if self.context.get(LOGGER):
                self.context.get(LOGGER).error(str(e))
            self.agent.status = self.status
            raise
        else:
            self.agent.status = self.status

