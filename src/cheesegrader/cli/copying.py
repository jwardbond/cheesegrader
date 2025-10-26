import csv
from pathlib import Path

import typer

from cheesegrader.cli.utils import ERROR_FG, SUCCESS_FG, WARN_FG, create_confirm, create_prompt
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
    typer.secho("=== COPY TOOL ===", bold=True)

    input_filepath = prompt_input_path("Input file path")

    # Load student list
    student_data, headers = prompt_get_csv()

    # Select which columns to use when creating name
    name_fields = prompt_select_headers(headers)

    # Get destination path
    dest_dir = prompt_input_path("Input the destination folder")

    if prompt_confirm_proceed(input_filepath, dest_dir, name_fields):
        # Copy folders
        typer.secho("Copying files...", fg=WARN_FG)
        copy_rename(input_filepath, student_data, name_fields, dest_dir)
        typer.secho("Files copied", fg=SUCCESS_FG)

        return


def prompt_input_path(prompt_text: str) -> Path:
    """Prompt the user for a path and validate that it exists."""
    while True:
        path_str = prompt(prompt_text).strip().strip('"')
        path = Path(path_str).resolve()
        if path.exists():
            return path
        else:
            typer.secho("Path does not exist!", fg=WARN_FG)
            typer.secho("Creating directory...", fg=WARN_FG)
            path.mkdir(parents=True, exist_ok=True)
            typer.secho(f"Created directory at {path}", fg=SUCCESS_FG)
            return path


def prompt_get_csv() -> tuple[list, Path, dict]:
    """Prompt user to input a CSV file path and returns its contents as a list of dicts.

    If the csv is missing required headers, prompts the user to map existing headers to required ones.

    Args:
        required_headers (set[str]): A set of required column headers.

    Returns:
        data: list[dict]: A list of {header: value} dicts representing CSV rows.
    """
    while True:
        path_str = prompt("Enter Student List CSV Path").strip().strip('"')
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

        return data, headers


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


def prompt_select_header(headers: list[str]) -> str:
    """Select a header (column) from a list."""
    while True:
        for i, h in enumerate(headers):
            typer.echo(f"\t[{i}] {h}")
        selection = prompt("Select column:", type=int)

        if selection in range(len(headers)):
            return headers[selection]
        typer.secho("Invalid selection", fg=ERROR_FG)


def prompt_confirm_proceed(
    input_filepath: Path,
    dest_dir: Path,
    name_fields: list[str],
) -> bool:
    """Prompt the user to confirm proceeding with the copy operation."""
    typer.secho("Please confirm the following settings:")
    typer.secho(f"\tInput file to copy: {input_filepath}")
    typer.secho(f"\tDestination directory: {dest_dir}")

    # Construct sample filename
    base = input_filepath.stem
    suffix = input_filepath.suffix
    filename = [f"[{field}]" for field in name_fields]
    filename = "_".join(filename)
    filename = filename + "_" + base + suffix
    filename = filename.replace(" ", "_")  # remove any lingering spaces
    filename = filename.lower()
    typer.secho(f"\tFile names: {filename}")

    response = confirm("Proceed with copying files?")

    return response
