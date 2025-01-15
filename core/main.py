from core.config import AppConfig
from core.cli import (
    console,
    display_missing_arguments_error,
    print_pipeline_help,
    print_available_plugins,
    print_basic_args_help,
    print_opsbox_banner,
    print_pipeline_building_help,
    print_config_help,
    print_welcome_message,
)
from core.plugins import Registry, PluginNotFoundError
from loguru import logger
import sys
from json import JSONDecodeError

from sys import argv


def start_logging(log_level: str = "INFO", log_file: str = None):
    """Start logging to a file."""
    logger.add(sys.stdout, level=log_level, colorize=True, diagnose=True, enqueue=True)
    if log_file is not None:
        logger.add(log_file, level=log_level, rotation="10 MB", compression="zip", serialize=True)
    logger.debug("Logging started")


def main():
    """Main entry point for the application."""
    # start logging
    logger.remove()

    if "--init-debug" in argv:
        start_logging(log_level="DEBUG")
        logger.debug("Initialization debugging enabled!")

    # parse args
    app_config = AppConfig()
    try:
        if "--help" in argv:
            del argv[argv.index("--help")]
            still_needed = app_config.fetch_missing_fields()
            if still_needed is not None:
                modules = app_config.basic_settings.modules
                print_pipeline_help(modules, still_needed)
                sys.exit(1)
            else:
                available_plugins = app_config.fetch_available_plugins()
                print_opsbox_banner()
                print_welcome_message()
                print_pipeline_building_help()
                print_config_help()
                print_basic_args_help()
                print_available_plugins(available_plugins, plugin_dir=app_config.basic_settings.plugin_dir)
                sys.exit(1)
        else:
            still_needed = app_config.load()
        if app_config.basic_settings.log_level is not None:
            start_logging(app_config.basic_settings.log_level, app_config.basic_settings.log_file)
        else:
            start_logging()
    except IndexError as _:
        print_opsbox_banner()
        display_text = """[bold red]It seems like you have your pipeline incorrectly specified! Please check the help below.\n[/bold red]"""
        console.print(display_text)
        print_pipeline_building_help()
        return 1
    except JSONDecodeError as e:
        print_opsbox_banner()
        console.print(f"[bold red]It seems like your configuration JSON is malformed![/bold red]\nError: {e}")
        return 1
    except FileNotFoundError as e:
        print_opsbox_banner()
        console.print(f"[bold red]It seems like you gave an incorrect path to your configuration![/bold red]\n{e}\n")
        print_config_help()
        return 1
    except PluginNotFoundError as e:
        print_opsbox_banner()
        if app_config.basic_settings.plugin_dir is not None:
            markup = f"""[bold red]It seems like one or more plugins you specified were not able to be found![/bold red]

[bold red]Please check the active plugin_dir {app_config.basic_settings.plugin_dir}.[/bold red]

Error: {e}
"""
        else:
            markup = f"""[bold red]It seems like one or more plugins you specified were not able to be found![/bold red]

[bold red]Please check the virtual environment for your desired plugin packages.[/bold red]

Error: {e}
"""
        console.print(markup)
        print_available_plugins(app_config.fetch_available_plugins(), plugin_dir=app_config.basic_settings.plugin_dir)
        return 1
    if still_needed:
        print_opsbox_banner()
        modules = app_config.basic_settings.modules
        display_missing_arguments_error(modules, still_needed)
        return 1

    pipeline = Registry().produce_pipeline()
    Registry().process_pipeline(pipeline)


if __name__ == "__main__":
    main()
