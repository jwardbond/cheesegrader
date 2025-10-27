import csv
import os
from collections.abc import Callable
from pathlib import Path

import typer

from cheesegrader.api_tools import QuercusAssignment, QuercusCourse

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
        typer.echo()

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

            # Remove text from args so not duplicated
            if args:
                args = args[1:]

            response = typer.prompt("", *args, **kwargs).strip().lower()
            typer.echo()

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


def prompt_get_csv(prompt_text: str) -> tuple[list, Path, dict]:
    """Prompt user to input a CSV file path and returns its contents as a list of dicts."""
    help_msg = """
    Help Menu:
        Enter the full path to the CSV file.

        ---
        Enter 'q' or press ctrl+c to quit at any time.
        Enter 'h' for help.
    """
    prompt = create_prompt(help_msg)

    while True:
        typer.echo(prompt_text)
        path_str = prompt("CSV path").strip().strip('"')
        path = Path(path_str)

        # Validate filepath
        if not path.exists():
            typer.secho("File does not exist!", fg=typer.colors.RED)
            continue
        if path.suffix.lower() != ".csv":
            typer.secho("File is not a CSV!", fg=typer.colors.RED)
            continue

        # Read CSV contents
        with path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            data = list(reader)

        return data, headers, path


def prompt_select_header(headers: list[str]) -> str:
    """Select a header (column) from a list."""
    help_msg = """
    Help Menu:
        Enter the number corresponding to the column you want to select.

        ---
        Enter 'q' or press ctrl+c to quit at any time.
        Enter 'h' for help.
    """
    prompt = create_prompt(help_msg)

    while True:
        for i, h in enumerate(headers):
            typer.echo(f"\t[{i}] {h}")
        selection = prompt("Select column:", type=int)

        if selection in range(len(headers)):
            return headers[selection]
        typer.secho("Invalid selection", fg=ERROR_FG)


def prompt_input_dir(prompt_text: str) -> Path:
    """Prompt the user for a path to a directory and validate that it exists."""
    help_msg = """
    Help Menu:
        Enter the full path to the desired directory.

        ---
        Enter 'q' or press ctrl+c to quit at any time.
        Enter 'h' for help.
    """
    prompt = create_prompt(help_msg)

    while True:
        typer.echo(prompt_text)
        path_str = prompt("Directory path").strip().strip('"')
        path = Path(path_str).resolve()
        if path.exists():
            return path

        typer.secho("Directory does not exist!", fg=WARN_FG)
        typer.secho("Creating directory...", fg=WARN_FG)
        path.mkdir(parents=True, exist_ok=True)
        typer.secho(f"Created directory at {path}", fg=SUCCESS_FG)
        return path


def prompt_setup_course() -> QuercusCourse:
    """Prompt the user to set up a QuercusCourse object."""
    help_msg = """
    Help Menu:
        Enter the Course ID for the Quercus course you want to set up.

        The easiest way to find this is to log into Quercus, navigate to the course, and look at the URL.

        ---
        Enter 'q' or press ctrl+c to quit at any time.
        Enter 'h' for help.
    """
    prompt = create_prompt(help_msg)

    typer.echo("Enter The Course ID.")
    course_id = prompt("Course ID")
    typer.echo("Loading course...")
    course = QuercusCourse(course_id, token=os.getenv("CG_TOKEN"))
    typer.secho(f"Loaded course: {course.course_name} ({course_id})\n", fg=SUCCESS_FG)

    return course


def prompt_setup_assignment(course: QuercusCourse) -> QuercusAssignment:
    """Prompt the user to set up a QuercusAssignment object."""
    help_msg = """
    Help Menu:
        Enter the Assignment ID for the Quercus assignment you want to set up.

        The easiest way to find this is to log into Quercus, navigate to the assignment, and look at the URL.

        ---
        Enter 'q' or press ctrl+c to quit at any time.
        Enter 'h' for help.
    """
    prompt = create_prompt(help_msg)

    typer.echo("Enter the Assignment ID.")
    assignment_id = prompt("Assignment ID")
    typer.echo("Loading assignment...")
    assignment = QuercusAssignment(course.course_id, assignment_id, token=os.getenv("CG_TOKEN"))
    typer.secho(f"Loaded assignment: {assignment.assignment_name} ({assignment_id})\n", fg=SUCCESS_FG)

    return assignment
