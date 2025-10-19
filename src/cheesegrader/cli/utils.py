from collections.abc import Callable

import typer

HELP_REGISTRY = {}
DEFAULT_HELP_MSG = "Enter 'q' or press ctrl+c to quit at any time.\nEnter 'h' for help."

# Prompt styles
PROMPT_BG = typer.colors.YELLOW
PROMPT_FG = typer.colors.BLACK

# Help message styles
HELP_FG = typer.colors.CYAN
HELP_BG = typer.colors.CYAN

# General styles
ERROR_FG = typer.colors.RED
SUCCESS_FG = typer.colors.GREEN
WARN_FG = typer.colors.YELLOW


def create_prompt(help_msg: str) -> Callable[..., str]:
    """Creates a function to replace typer.prompt.

    Adds a help message and the option to enter 'q' to quit.
    """

    def patched_prompt(*args, **kwargs) -> str:  # noqa: ANN002, ANN003
        prompt_text = args[0] if args else kwargs.get("text", "")
        typer.echo()
        typer.secho(prompt_text, fg=PROMPT_FG, bg=PROMPT_BG, nl=False)

        # Remove text from args so not duplicated
        if args:
            args = args[1:]

        response = typer.prompt("", *args, **kwargs)

        if isinstance(response, str):
            if response.lower() == "h":
                typer.secho(help_msg, fg=HELP_FG)
                typer.echo()
                typer.secho("Press any key to continue", fg=PROMPT_FG, bg=HELP_BG, nl=False)
                input()

            if response.lower() == "q":
                raise typer.Exit

        return response

    return patched_prompt


def create_confirm(help_msg: str) -> Callable[..., str]:
    """Creates a function to replace typer.confirm.

    Adds a help message and the option to enter 'q' to quit.
    """

    def patched_confirm(*args, **kwargs) -> str:  # noqa: ANN002, ANN003
        while True:
            prompt_text = args[0] if args else kwargs.get("text", "")
            typer.echo()
            typer.secho(prompt_text + " [y/n]", fg=PROMPT_FG, bg=PROMPT_BG, nl=False)

            response = typer.prompt("").strip().lower()

            if response in ("y", "yes"):
                return True
            elif response in ("n", "no"):
                return False
            elif response == "h":
                typer.secho(help_msg, fg=HELP_FG)
            elif response == "q":
                typer.Exit()
            else:
                typer.secho("Invalid input. Enter 'y', 'n', or 'h'.", fg=ERROR_FG)

    return patched_confirm
