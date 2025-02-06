from rich.console import Console
from rich.align import Align
from rich.table import Table
from rich.text import Text
from pydantic.fields import FieldInfo
from opsbox.config import ApplicationSettings

console = Console()

ascii_art = """
  ____  ___  _______  ____  _  __
 / __ \\/ _ \\/ __/ _ )/ __ \\| |/_/
/ /_/ / ___/\\ \\/ _  / /_/ />  <  
\\____/_/  /___/____/\\____/_/|_|  
                                 
"""

pipeline_building_help = Text.from_markup(
    """Opsbox uses a series of modules specified at runtime to analyze different environments.
These modules [bold]have their own[/bold] arguments and required settings that will be looked for upon startup, and [bold]must be specified as a pipeline in the following format:[/bold]

[bold]input_1,input_2-assistant_1-assistant_2-output_1,output_2[/bold]

Where:
    - The first arguments are the input (normally rego) plugins we want to use, separated with a comma
    - The middle arguments are the assistants we want to use, separated by a hyphen
    - The last arguments are the outputs we want to use, separated by a comma

For instance, if we wanted to check for stray EBS volumes and output the results to the main after running through a cost assistant, we would need to use the following pipeline:

[bold]opsbox --modules stray_ebs-cost_savings-cli_out ...[/bold]
""",
    style="yellow",
)

config_help = Text.from_markup(
    """Opsbox can be configured through either:
    - A JSON file, with arguments as the keys of a dictionary,
    - Environment variables, with the arguments as the variable names, or
    - Command line arguments, with the arguments as the flags accompanied by their respective values.

First, command line values will be loaded, then any JSON file sepcified by the [bold]--config[/bold] flag, then environment variables.

Default values can be set in [bold]~/.opsbox.json[/bold], which will be loaded upon startup before other configuration files.
    """,
    style="cyan",
)

welcome_message = Text.from_markup(
    """Welcome to Opsbox! This is a tool for analyzing and reporting on cloud environments using configurable pipelines and powerful plugins.
    
If you need help with a specific pipeline, please use the [bold]--help[/bold] flag alongside the pipeline to get more information.
    """,
    style="green",
)


def print_plugin_not_found_error(plugin_dir: str | None, e: Exception):
    """Print an error message for when a plugin is not found.

    Args:
        plugin_dir (str | None): The plugin directory that was searched.
        e (Exception): The exception that was raised."""
    if plugin_dir is not None:
        markup = f"""[bold red]It seems like one or more plugins you specified were not able to be found![/bold red]

[bold red]Please check the active plugin_dir {plugin_dir}.[/bold red]

Error: {e}
"""
    else:
        markup = f"""[bold red]It seems like one or more plugins you specified were not able to be found![/bold red]

[bold red]Please check the virtual environment for your desired plugin packages.[/bold red]

Error: {e}
"""
    console.print(markup)


def print_missing_arguments_error(modules: list[str], arguments: list[tuple[str, str, FieldInfo]]):
    """Display a table of missing arguments for a given pipeline.

    Args:
        modules (list[str]): The modules that are missing arguments.
        arguments (list[tuple[str, str, FieldInfo]]): A list of tuples containing the missing argument name,
            plugin name, and field info.
    """
    markup = f"[bold red]You are missing arguments for pipeline [/bold red][bold purple4]{'-'.join(modules)}[/bold purple4]!\n\n"
    console.print(markup)

    table = Table(
        title=f"[bold red]Missing Arguments for pipeline [bold purple4]{'-'.join(modules)}[/bold purple4][/bold red]",
        caption="[bold]Please add the following arguments to your configuration to continue.[/bold]",
        title_justify="center",
    )
    table.add_column("Argument Name", justify="left", style="cyan")
    table.add_column("Plugin Name", justify="left", style="green")
    table.add_column("Description", justify="left", style="magenta")

    for arg_name, plugin_name, field_info in arguments:
        table.add_row(arg_name, plugin_name, field_info.description)

    console.print(table)
    console.print("\n")
    print_config_help()


def print_available_plugins(plugins: list[tuple[str, str]], excluded: list[str] | None = ["handler", "provider"], plugin_dir: str = None):
    """Print a list of available plugins.

    Args:
        plugins (list[tuple[str, str]]): A list of tuples containing the plugin name and type.
        excluded (list[str], optional): A list of plugin types to exclude. Defaults to ["handler", "provider"].
        plugin_dir (str, optional): The plugin directory that was searched. Defaults to None.
    """
    # Sort the plugins by type
    if excluded is None:
        excluded = []
    plugins = [plugins for plugins in plugins if plugins[1] not in excluded]
    plugins.sort(key=lambda x: x[1])
    plugins.reverse()

    console.rule("[bold red]Environment Plugins[/bold red]")
    if len(plugins) == 0:  # No plugins found
        if plugin_dir:
            markup = f"""[italic violet]Hmm, it seems like there are no plugins in the directory {plugin_dir}!

Check your plugin directiory and try again! [/italic violet]"""
        else:
            markup = """[italic violet]Hmm, it seems like there are no plugins in your virtual environment!
            
Try installing some opsbox packages into your virtual environment or specifying a plugin directory using the plugin_dir argument. [/italic violet]"""
        console.print(markup)
    else:  # Plugins found, print table of plugins
        caption = f"[bold]Here is a list of plugins available in {plugin_dir}.[/bold]" if plugin_dir else "[bold]Here is a list of plugins available in your virtual environment.[/bold]"
        table = Table(
            title_justify="center",
            caption=caption,
        )
        table.add_column("Plugin Name", justify="left", style="cyan")
        table.add_column("Type", justify="left", style="green")

        for plugin_name, plugin_type in plugins:
            table.add_row(plugin_name, plugin_type)

        table = Align.left(table, vertical="middle")
        console.print(table)


def print_pipeline_building_help():
    """Print the pipeline building help."""
    console.rule("[bold red]Pipeline Building Help[/bold red]")
    console.print(pipeline_building_help)


def print_config_help():
    """Print the configuration help."""
    console.rule("[bold red]Configuration Help[/bold red]")
    console.print(config_help)


def print_opsbox_banner():
    """Print the OpsBox banner."""
    # Create a Text object and add the ASCII art with light blue color
    light_blue_text = Text(ascii_art, style="cyan", justify="center")
    light_blue_text = Align.left(light_blue_text, vertical="middle")

    console.print(light_blue_text)


def print_welcome_message():
    """Print the welcome message."""
    console.print(welcome_message)


def print_basic_args_help():
    """Print the help for the basic arguments."""

    table = Table(
        caption="[bold]Here is a list of opsbox.arguments for the application.[/bold]",
    )
    table.add_column("Argument Name", justify="left", style="cyan")
    table.add_column("Description", justify="left", style="magenta")
    table.add_column("Required", justify="left", style="yellow")

    for field_name, field_info in ApplicationSettings.__fields__.items():
        table.add_row(field_name, field_info.description, str(field_info.is_required()))

    table = Align.left(table, vertical="middle")

    console.rule("[bold red]Opsbox opsbox.Arguments[/bold red]")
    console.print(table)


def print_pipeline_help(modules: list[str], models: list[tuple[str, str, FieldInfo]]):
    """Print the help for a given pipeline.

    Args:
        modules (list[str]): The modules that are currently loaded.
        models (list[tuple[type[BaseModel], str]]): A list of tuples containing the model and plugin name.
    """
    # Create a Text object and add the ASCII art with light blue color
    light_blue_text = Text(ascii_art, style="cyan", justify="center")
    console.print(light_blue_text)

    # Pipeline info
    mod_str = f"[blue]Viewing the help for the following pipeline: [bold purple4]{'-'.join(modules)}[/bold purple4]\n"
    console.print(mod_str)

    # Table of arguments
    table = Table(
        title="[bold red]Arguments[/bold red]",
        caption="""[bold]Here are a list of potential arguments for the given pipeline.
Reconfigure your pipeline to see more arguments.[/bold]""",
    )
    table.add_column("Argument Name", justify="left", style="cyan")
    table.add_column("Plugin Name", justify="left", style="green")
    table.add_column("Description", justify="left", style="magenta")
    table.add_column("Required", justify="left", style="yellow")

    for field_name, plugin_name, field_info in models:
        table.add_row(field_name, plugin_name, field_info.description, str(field_info.is_required()))

    table = Align.left(table, vertical="middle")
    console.print(table)

    # Reminder to view documentation
    doc_str = "\n[bold]For more information, please refer to the documentation found at the `opsbox-docs` repo.[/bold]"
    console.print(doc_str)
