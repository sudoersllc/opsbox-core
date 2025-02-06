from opsbox.config import AppConfig
from opsbox.cli import (
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
from opsbox.plugins import Registry, PluginNotFoundError
from loguru import logger
import sys
from json import JSONDecodeError

from sys import argv

import yaml


def verbose_formatter(record):
    """Format the log record for the CLI."""
    format_str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS Z}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>\n"

    # if we have an extra dict, we want to filter out all double underscore keys
    if "extra" in record:
        extra_fields = {k: v for k, v in record["extra"].items() if "__" not in k}
        if extra_fields == {}:  # if there are no extra fields, return the format string
            return format_str
        else:
            # format as yaml
            extra_str = yaml.dump(extra_fields["extra"], default_flow_style=False, sort_keys=False)

            # remove the newline at the end and chars that could trip up str.format
            extra_str = extra_str.replace("{", "").replace("}", "")
            extra_str = f"<magenta>Extra Data:\n</magenta><yellow>{extra_str}</yellow>"
            format_str = f"{format_str}{extra_str}"

    return format_str


def start_logging(log_level: str | None = None, log_file: str | None = None, verbose: bool = False):
    """Start logging to a file.

    Args:
        log_level (str, optional): The log level to log at. Defaults to "INFO".
        log_file (str, optional): The log file to log to. Defaults to None
    """
    if log_level is None:
        log_level = "INFO"

    if verbose:
        logger.add(sys.stdout, level=log_level, colorize=True, diagnose=True, enqueue=True, format=verbose_formatter)
        logger.debug("Started verbose logging to stdout.")
    else:
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
    if "--init_debug" in argv:
        start_logging(log_level="TRACE")

    # if no args are passed, print help
    if len(argv) <= 1:
        argv.append("--help")  # add --help to args

    # load help and config
    try:
        # init settings
        app_config = AppConfig()  # setup config singleton
        app_config.init_settings()  # initialize settings

        # init logger
        logger.remove()  # re-initialize logger
        start_logging(app_config.basic_settings.log_level, app_config.basic_settings.log_file, app_config.basic_settings.verbose)

        # load config
        missing_fields = app_config.load(all_fields=app_config.basic_settings.help)
        if app_config.basic_settings.help:  # if --help is passed, print help
            if missing_fields is not None:
                # if there are missing fields and a pipeline, print pipeline help
                modules = app_config.basic_settings.modules
                print_pipeline_help(modules, missing_fields)
                sys.exit(1)
            else:
                # if there are no missing fields, print general help
                available_plugins = app_config.grab_conf_environment_plugins()
                print_opsbox_banner()
                print_welcome_message()
                print_pipeline_building_help()
                print_config_help()
                print_basic_args_help()
                print_available_plugins(available_plugins, excluded=(None if "--see_all" in argv else ["handler", "provider"]), plugin_dir=app_config.basic_settings.plugin_dir)
                sys.exit(1)
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
        print_available_plugins(app_config.grab_conf_environment_plugins(), excluded=(None if "--see_all" in argv else ["handler", "provider"]), plugin_dir=app_config.basic_settings.plugin_dir)
        return 1
    if missing_fields:  # if there are still missing fields
        print_opsbox_banner()
        print_missing_arguments_error(app_config.basic_settings.modules, missing_fields)
        return 1

    # process pipeline
    Registry().process_pipeline()


if __name__ == "__main__":
    main()
