from core.config import AppConfig
from core.cli import (
    console,
    print_missing_arguments_error,
    print_pipeline_help,
    print_available_plugins,
    print_basic_args_help,
    print_opsbox_banner,
    print_pipeline_building_help,
    print_config_help,
    print_welcome_message,
    print_plugin_not_found_error,
)
from core.plugins import Registry, PluginNotFoundError
from loguru import logger
import sys
from json import JSONDecodeError

from sys import argv
import contextlib


def start_logging(log_level: str = "INFO", log_file: str = None):
    """Start logging to a file.

    Args:
        log_level (str): The log level to use.
        log_file (str): The file to log to.
    """
    logger.add(sys.stdout, level=log_level, colorize=True, diagnose=True, enqueue=True)
    logger.debug("Started logging to stdout.")
    if log_file is not None:
        logger.add(log_file, level=log_level, rotation="10 MB", compression="zip", serialize=True)
        logger.debug(f"Started logging to {log_file}.")


def main():
    """Main entry point for the application."""
    # remove the default logger
    logger.remove()

    # check for debug flag
    if "--init-debug" in argv:
        start_logging(log_level="TRACE")
        logger.debug("Initialization debugging enabled!")
        del argv[argv.index("--init-debug")]

    # check for see-all flag
    if "--see-all" in argv:
        del argv[argv.index("--see-all")]
        excluded = None
    else:
        excluded = ["handler", "provider"]

    # setup config singleton
    app_config = AppConfig()

    # load help and config
    try:
        if "--help" in argv or len(argv) == 1:  # if no args are passed or --help is passed
            with contextlib.suppress(ValueError):  # remove --help from argv
                del argv[argv.index("--help")]
            missing_fields = app_config.fetch_missing_fields()
            if missing_fields is not None:  # if there are still missing fields, print pipeline help
                modules = app_config.basic_settings.modules
                print_pipeline_help(modules, missing_fields)
                sys.exit(1)
            else:  # if there are no missing fields, print help
                available_plugins = app_config.fetch_available_plugins()
                print_opsbox_banner()
                print_welcome_message()
                print_pipeline_building_help()
                print_config_help()
                print_basic_args_help()                    
                print_available_plugins(available_plugins, excluded=excluded, plugin_dir=app_config.basic_settings.plugin_dir)
                sys.exit(1)
        else:  # if args are passed, load the config
            missing_fields = app_config.load()

        # start logging
        if app_config.basic_settings.log_level is not None:
            start_logging(app_config.basic_settings.log_level, app_config.basic_settings.log_file)
        else:
            start_logging()
    except IndexError as _:  # if the pipeline is incorrectly specified
        print_opsbox_banner()
        display_text = """[bold red]It seems like you have your pipeline incorrectly specified! Please check the help below.\n[/bold red]"""
        console.print(display_text)
        print_pipeline_building_help()
        return 1
    except JSONDecodeError as e:  # if the config is malformed
        print_opsbox_banner()
        console.print(f"[bold red]It seems like your configuration JSON is malformed![/bold red]\nError: {e}\n")
        print_config_help()
        return 1
    except FileNotFoundError as e:  # if the config file is not found
        print_opsbox_banner()
        console.print(f"[bold red]It seems like you gave an incorrect path to your configuration![/bold red]\nError: {e}\n")
        print_config_help()
        return 1
    except PluginNotFoundError as e:  # if a plugin is not found
        print_opsbox_banner()
        print_plugin_not_found_error(app_config.basic_settings.plugin_dir, e)        
        print_available_plugins(app_config.fetch_available_plugins(), excluded=excluded, plugin_dir=app_config.basic_settings.plugin_dir)
        return 1
    if missing_fields:  # if there are still missing fields
        print_opsbox_banner()
        print_missing_arguments_error(app_config.basic_settings.modules, missing_fields)
        return 1

    # process pipeline
    pipeline = Registry().produce_pipeline()
    Registry().process_pipeline(pipeline)


if __name__ == "__main__":
    main()
