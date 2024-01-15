import argparse
from werkzeug.serving import run_simple
from .app import create_app


def run():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("port", default=8000, type=int, nargs="?")
    argparser.add_argument(
        "--config", "-c", default="serverless.yml", help="serverless.yml config."
    )
    argparser.add_argument(
        "--version", "-v", default="2.0", help="API Gateway payload version."
    )
    argparser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        required=False,
        help="Enable the debugger.",
    )
    argparser.add_argument(
        "--reload",
        "-r",
        action="store_true",
        required=False,
        help="Enable the reloader.",
    )
    args = argparser.parse_args()

    app = create_app(args.config, payload_version=args.version)
    run_simple(
        "127.0.0.1", args.port, app, use_debugger=args.debug, use_reloader=args.reload
    )
