import csv
from pathlib import Path

import typer

from cheesegrader.cli.utils import (
    ERROR_FG,
    SUCCESS_FG,
    WARN_FG,
    create_confirm,
    create_prompt,
    prompt_get_csv,
    prompt_input_dir,
    prompt_select_header,
)
from cheesegrader.utils import copy_rename

HELP_TEXT = """
Help Menu:
    This module is for copying and renaming a file based on a student list.

    You will need at least:
        - A file to copy
        - A csv file with student information that will be used to rename the files

    For best results, make sure your csv is clean (no columns with blank headers, no duplicate columns no cells with just spaces, etc.)

    ---
    Enter 'q' or press ctrl+c to quit at any time.
    Enter 'h' for help.
"""

app = typer.Typer(help="Copying workflow")

prompt = create_prompt(HELP_TEXT)
confirm = create_confirm(HELP_TEXT)

# Example directories — adjust as needed
FILES_DIR = Path("data/files")
STUDENT_LISTS_DIR = Path("data/student_lists")


def run() -> None:
    typer.secho("\n=== COPY TOOL ===\n", bold=True)

    input_filepath = prompt_input_filepath("Enter the path to the file to be copied.")

    # Load student list
    student_data, headers, csv_path = prompt_get_csv("Enter the path to the student list .csv file.")

    # Select which columns to use when creating name
    name_fields = prompt_select_headers(headers)

    # Get destination path
    dest_dir = prompt_input_dir("Input the destination folder")

    if prompt_confirm_copy(input_filepath, dest_dir, csv_path, name_fields):
        # Copy folders
        typer.secho("Copying files...", fg=WARN_FG)
        copy_rename(input_filepath, student_data, name_fields, dest_dir)
        typer.secho("Files copied", fg=SUCCESS_FG)

        return


def prompt_input_filepath(prompt_text: str) -> Path:
    """Prompt the user for a path to a file and validate that it exists."""
    while True:
        typer.echo(prompt_text)
        path_str = prompt("Filepath").strip().strip('"')
        path = Path(path_str).resolve()
        if path.exists():
            return path
        typer.secho(f"File not found at {path.resolve()}! Try again.", fg=ERROR_FG)


def prompt_select_headers(headers: list[str]) -> list[str]:
    """Let the user select multiple headers from the list using prompt_select_header."""
    selected = []
    remaining = list(headers)

    typer.secho("Select columns to use when renaming files (pick one at a time):")
    typer.secho("Whatever is in these columns will be prepended to the file name.")

    while remaining:
        header = prompt_select_header(remaining)
        selected.append(header)
        remaining.remove(header)

        if not remaining:
            break
        if not confirm("Select another column?"):
            break

    return selected


def prompt_confirm_copy(
    input_filepath: Path,
    dest_dir: Path,
    csv_path: Path,
    name_fields: list[str],
) -> bool:
    """Prompt the user to confirm proceeding with the copy operation."""
    typer.echo("Please confirm the following settings:")
    typer.echo(f"\tInput file to copy: {input_filepath}")
    typer.echo(f"\tDestination directory: {dest_dir}")
    typer.echo(f"\tCSV being used for renaming: {csv_path}")

    # Construct sample filename
    base = input_filepath.stem
    suffix = input_filepath.suffix
    filename = [f"[{field}]" for field in name_fields]
    filename = "_".join(filename)
    filename = filename + "_" + base + suffix
    filename = filename.replace(" ", "_")  # remove any lingering spaces
    filename = filename.lower()
    typer.echo(f"\tFile name example: {filename}")

    return confirm("Is this information correct?")
