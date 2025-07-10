import argparse
import os

from ufo.config.config import Config
from ufo.simple_app_agent import SimpleAppAgent
from ufo.simple_context import SimpleContext, APPLICATION_WINDOW
from ufo.automator.ui_control.inspector import ControlInspectorFacade

configs = Config.get_instance().config_data


class SimpleAppAgentRunner:
    """Initialize and run an :class:`AppAgent` without a HostAgent."""

    def __init__(self, process_name: str, app_root_name: str, request: str):
        self.process_name = process_name
        self.app_root_name = app_root_name
        self.request = request
        self.app_agent = self._init_app_agent()

    def _init_app_agent(self) -> SimpleAppAgent:
        """Create a :class:`SimpleAppAgent` using config defaults."""
        return SimpleAppAgent.from_config(
            self.process_name, self.app_root_name, self.request
        )

    def run(self) -> None:
        """Drive the underlying :class:`AppAgent` until completion."""

        log_dir = os.path.join("logs", "simple_runner")
        context = SimpleContext.simple(
            self.process_name, self.app_root_name, self.request, log_dir=log_dir
        )

        inspector = ControlInspectorFacade()
        windows = inspector.get_desktop_app_dict(remove_empty=True)
        app_window = None
        lower_process = self.process_name.lower()
        lower_root = self.app_root_name.lower()
        for window in windows.values():
            title = window.element_info.name.lower()
            if lower_process in title or lower_root in title:
                app_window = window
                break

        if app_window is None:
            available = ", ".join(w.element_info.name for w in windows.values())
            raise RuntimeError(
                f"Application window matching '{self.process_name}' or '{self.app_root_name}' not found. "
                f"Available windows: {available}"
            )

        context.set(APPLICATION_WINDOW, app_window)

        while not self.app_agent.is_finished:
            self.app_agent.process(context)

def main() -> None:
    parser = argparse.ArgumentParser(description="Run a single AppAgent")
    parser.add_argument("--process", required=True, help="Application process name")
    parser.add_argument("--root", required=True, help="Application root name")
    parser.add_argument("--request", required=True, help="User request")
    args = parser.parse_args()
    runner = SimpleAppAgentRunner(args.process, args.root, args.request)
    runner.run()


if __name__ == "__main__":
    main()
