import argparse
import os
import time

from ufo.config.config import Config
from ufo.simple_app_agent import SimpleAppAgent
from ufo.simple_context import SimpleContext, APPLICATION_WINDOW
from ufo.automator.ui_control.inspector import ControlInspectorFacade


configs = Config.get_instance().config_data


def run_dummy_cycle(
    process_name: str, app_root_name: str, request: str = "", steps: int = 1
) -> None:
    """Run an AppAgent for a limited number of steps using its native process."""

    app_agent = SimpleAppAgent.from_config(process_name, app_root_name, request)

    app_agent.context_provision(request)

    log_dir = os.path.join("logs", "dummy_cycle")
    context = SimpleContext.simple(
        process_name, app_root_name, request, log_dir=log_dir
    )

    inspector = ControlInspectorFacade()
    windows = inspector.get_desktop_app_dict(remove_empty=True)
    app_window = None
    lower_process = process_name.lower()
    lower_root = app_root_name.lower()
    for window in windows.values():
        title = window.element_info.name.lower()
        if lower_process in title or lower_root in title:
            app_window = window
            break

    if app_window is None:
        available = ", ".join(w.element_info.name for w in windows.values())
        raise RuntimeError(
            f"Application window matching '{process_name}' or '{app_root_name}' not found. "
            f"Available windows: {available}"
        )

    context.set(APPLICATION_WINDOW, app_window)


    step = 0
    while step < steps and not app_agent.is_finished:
        print(f"Step {step + 1}: running AppAgent ...")
        app_agent.process(context)

        step += 1
        time.sleep(1)

    print("Cycle completed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Demonstrate the ground-decide-act loop with dummy actions"
    )
    parser.add_argument("--process", required=True, help="Application process name")
    parser.add_argument("--root", required=True, help="Application root name")
    parser.add_argument("--request", default="", help="Optional request text")
    parser.add_argument("--steps", type=int, default=1, help="Number of loop iterations")
    args = parser.parse_args()
    run_dummy_cycle(args.process, args.root, args.request, args.steps)


if __name__ == "__main__":
    main()
