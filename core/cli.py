from rich.console import Console
from rich.table import Table
from rich.text import Text
from pydantic.fields import FieldInfo
from core.config import EssentialSettings

console = Console()


def display_missing_arguments_error(modules: list[str], arguments: list[tuple[str, str, FieldInfo]]):
    """Display a table of missing arguments for a given pipeline.

    Args:
        modules (list[str]): The modules that are missing arguments.
        arguments (list[tuple[str, str, FieldInfo]]): A list of tuples containing the missing argument name,
            plugin name, and field info.
    """
    table = Table(
        title=f"[bold red]Missing Arguments for pipeline [/bold red][bold purple4]{'-'.join(modules)}[/bold purple4]",
        caption="[bold]Please provide the following arguments to continue.[/bold]",
        title_justify="left",
        expand=True
    )
    table.add_column("Argument Name", justify="left", style="cyan")
    table.add_column("Plugin Name", justify="left", style="green")
    table.add_column("Description", justify="left", style="magenta")

    for arg_name, plugin_name, field_info in arguments:
        table.add_row(arg_name, plugin_name, field_info.description)

    console.print(table)

ascii_art = """
  ____  ___  _______  ____  _  __
 / __ \\/ _ \\/ __/ _ )/ __ \\| |/_/
/ /_/ / ___/\\ \\/ _  / /_/ />  <  
\\____/_/  /___/____/\\____/_/|_|  
                                 
"""

def print_available_plugins(plugins: list[tuple[str, str]]):
    """Print a list of available plugins.

    Args:
        plugins (list[tuple[str, str]]): A list of tuples containing the plugin name and type.
    """
    leader_text = Text("Here are the plugins available in your environment\n", style="bold", justify="center")
    console.print(leader_text)
    table = Table(
        title="[bold red]Available Plugins[/bold red]",
        title_justify="center",
        expand=True
    )
    table.add_column("Plugin Name", justify="left", style="cyan")
    table.add_column("Type", justify="left", style="green")

    for plugin_name, plugin_type in plugins:
        table.add_row(plugin_name, plugin_type)

    console.print(table)

def print_opsbox_banner():
    """Print the OpsBox banner."""
    # Create a Text object and add the ASCII art with light blue color
    light_blue_text = Text(ascii_art, style="cyan", justify="center")
    console.print(light_blue_text)
    leader_text = Text("Welcome to OpsBox!", style="green", justify="center")
    console.print(leader_text)

def print_basic_args_help():
    """Print the help for the basic arguments."""
    # Table of arguments
    cap_text = Text("Here's a list of potential arguments core to the application.\n", style="bold", justify="center")
    # justify center
    console.print(cap_text)
    table = Table(
        title="[bold red]Base Arguments[/bold red]",
        title_justify="center",
        expand=True
    )
    table.add_column("Argument Name", justify="left", style="cyan")
    table.add_column("Description", justify="left", style="magenta")
    table.add_column("Required", justify="left", style="yellow")

    for field_name, field_info in EssentialSettings.__fields__.items():
        table.add_row(field_name, field_info.description, str(field_info.is_required()))
    
    console.print(table)
    console.rule()


def print_pipeline_help(modules: list[str], models: list[tuple[str, str, FieldInfo]]):
    """Print the help for a given pipeline.

    Args:
        modules (list[str]): The modules that are currently loaded.
        models (list[tuple[type[BaseModel], str]]): A list of tuples containing the model and plugin name.
    """
    # ASCII Banner

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

    console.print(table)

    # Reminder to view documentation
    doc_str = (
        "\n[bold]For more information, please refer to the documentation found at the "
        "`opsbox-docs` repo.[/bold]"
    )
    console.print(doc_str)
