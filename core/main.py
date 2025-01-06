from core.config import AppConfig
from core.cli import console, display_missing_arguments_error, print_help
from core.plugins import Registry
from loguru import logger
import sys
from json import JSONDecodeError

from sys import argv


def start_logging():
    """Start logging to a file."""
    logger.remove()
    logger.add(sys.stdout, level="TRACE", colorize=True, diagnose=True, enqueue=True)
    logger.add("./log.json", level="DEBUG", rotation="10 MB", compression="zip", serialize=True)
    logger.debug("Logging started")


def main():
    """Main entry point for the application."""
    # start logging
    start_logging()

    # parse args
    app_config = AppConfig()
    try:
        if "--help" in argv:
            del argv[argv.index("--help")]
            still_needed = app_config.load_help()
            modules = app_config.basic_settings.modules
            print_help(modules, still_needed)
            sys.exit(1)
        else:
            still_needed = app_config.load()
    except JSONDecodeError as e:
        console.print(f"[bold red]Error validating JSON configuration: [/bold red] {e}")
        return 1
    except FileNotFoundError as e:
        console.print(f"[bold red]Error loading configuration file: [/bold red] {e}")
        return 1
    if still_needed:
        modules = app_config.basic_settings.modules
        display_missing_arguments_error(modules, still_needed)
        return 1

    # add stdout logger
    pipeline = Registry().produce_pipeline()
    Registry().process_pipeline(pipeline)


if __name__ == "__main__":
    main()
