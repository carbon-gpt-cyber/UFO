import argparse
from ufo.simple_app_agent import SimpleAppAgent
from ufo.simple_context import SimpleContext, APPLICATION_WINDOW
from ufo.automator.ui_control.inspector import ControlInspectorFacade


def run(process: str, root: str, request: str) -> None:
    """Launch a SimpleAppAgent and run until it finishes."""
    agent = SimpleAppAgent.from_config(process, root, request)
    context = SimpleContext.simple(process, root, request, log_dir="logs/minimal_example")
    window = ControlInspectorFacade().locate_window(process, root)
    context.set(APPLICATION_WINDOW, window)

    while not agent.is_finished:
        agent.process(context)
        if agent.processor is not None:
            print(agent.processor._response_json)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minimal AppAgent example")
    parser.add_argument("--process", required=True, help="Application process name")
    parser.add_argument("--root", required=True, help="Application root name")
    parser.add_argument("--request", required=True, help="User request")
    args = parser.parse_args()
    run(args.process, args.root, args.request)
