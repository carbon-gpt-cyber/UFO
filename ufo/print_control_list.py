import argparse
import os

from ufo.config.config import Config
from ufo.simple_app_agent import SimpleAppAgent
from ufo.simple_app_agent_processor import SimpleAppAgentProcessor
from ufo.simple_context import (
    SimpleContext,
    APPLICATION_WINDOW,
)
from ufo.automator.ui_control.inspector import ControlInspectorFacade

configs = Config.get_instance().config_data


def dump_controls(
    process_name: str,
    app_root_name: str,
    request: str = "",
    click: str | None = None,
) -> None:
    app_agent = SimpleAppAgent.from_config(process_name, app_root_name, request)

    log_dir = os.path.join("logs", "control_dump")
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
            f"Application window matching '{process_name}' or '{app_root_name}' "
            f"not found. Available windows: {available}"
        )

    context.set(APPLICATION_WINDOW, app_window)

    processor = SimpleAppAgentProcessor(agent=app_agent, context=context)
    processor.get_control_info()

    for info in processor.control_recorder.merged_controls_info:
        print(info)

    if click:
        label = click if click in processor._annotation_dict else None
        if label is None:
            target = click.lower()
            for info in processor.control_recorder.merged_controls_info:
                if target in str(info.get("control_text", "")).lower():
                    label = str(info.get("label"))
                    break

        if label is None or label not in processor._annotation_dict:
            raise RuntimeError(f"Control '{click}' not found")

        control = processor._annotation_dict[label]
        app_agent.Puppeteer.receiver_manager.create_ui_control_receiver(
            control, app_window
        )
        app_agent.Puppeteer.execute_command("click_input", {"button": "left"})

        print(f"Clicked control {label}: {click}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Print control list of an application")
    parser.add_argument("--process", required=True, help="Application process name")
    parser.add_argument("--root", required=True, help="Application root name")
    parser.add_argument("--request", default="", help="Optional request text")
    parser.add_argument(
        "--click", default=None, help="Label or text of a control to click"
    )
    args = parser.parse_args()
    dump_controls(args.process, args.root, args.request, args.click)


if __name__ == "__main__":
    main()
