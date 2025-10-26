import csv
from pathlib import Path

import typer

from cheesegrader.cli.utils import ERROR_FG, SUCCESS_FG, WARN_FG, create_confirm, create_prompt
from cheesegrader.utils import filesorter

HELP_TEXT = """
Help Menu:
    This module is for sorting files into folders based on a NAME:SUBFOLDER mapping.
    It searches for files in a source directory containing NAME, and if any are found,
    moves them into SUBFOLDER. This is useful for sorting student submissions, or named
    rubrics.

    You will need at least:
        - A folder containing the files to be sorted
        - A csv file with filename to folder mapping information

    For best results, make sure your csv is clean (no columns with blank headers, no duplicate columns no cells with just spaces, etc.)

    ---
    Enter 'q' or press ctrl+c to quit at any time.
    Enter 'h' for help.
"""

prompt = create_prompt(HELP_TEXT)
confirm = create_confirm(HELP_TEXT)


def run() -> None:
    typer.secho("=== SORTING TOOL ===", bold=True)

    while True:
        # Get source directory
        typer.echo("Enter the folder containing the files to be sorted.")
        source_dir = prompt_input_path("Enter source directory")

        # Get destination directory
        typer.secho("Enter the destination folder for sorted files.")
        dest_dir = prompt_input_path("Enter destination directory")

        # Get map file
        typer.echo("Enter the csv containing the filename -> folder mapping.")
        student_data, headers = prompt_get_csv()

        # Select the columns to use
        typer.echo("Select the column to use to identify files:")
        filename_field = prompt_select_header(headers)
        typer.echo("Select the column containing folder names")
        dir_field = prompt_select_header(headers)
        sort_map = create_sort_map(student_data, filename_field, dir_field)

        # Confirm operation
        if prompt_confirm_sort(source_dir, dest_dir, filename_field, dir_field):
            # Perform sorting
            typer.secho("Sorting files...")
            missing = filesorter(source_dir, dest_dir, sort_map)
            typer.secho("Sorting complete!", fg=SUCCESS_FG)

            if missing:
                typer.secho("The following files were not found:", fg=WARN_FG)
                for f in missing:
                    typer.secho(f"\t{f}", fg=WARN_FG)

            return


def prompt_input_path(prompt_text: str) -> Path:
    """Prompt the user for a path and validate that it exists."""
    while True:
        path_str = prompt(prompt_text).strip().strip('"')
        path = Path(path_str).resolve()
        if path.exists():
            return path

        typer.secho("Path does not exist!", fg=WARN_FG)
        typer.secho("Creating directory...", fg=WARN_FG)
        path.mkdir(parents=True, exist_ok=True)
        typer.secho(f"Created directory at {path}", fg=SUCCESS_FG)
        return path


def prompt_get_csv() -> tuple[list, Path, dict]:
    """Prompt user to input a CSV file path and returns its contents as a list of dicts."""
    while True:
        path_str = prompt("Enter the csv path").strip().strip('"')
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


def create_sort_map(data: list, filename_field: str, dir_field: str) -> dict:
    """Create a mapping of filenames to destination directories."""
    sort_map = {}
    for entry in data:
        filename = entry.get(filename_field, "").strip()
        dirname = entry.get(dir_field, "").strip()
        if filename and dirname:
            sort_map[filename] = dirname
        elif not filename:
            typer.secho(f"\tWarning: Missing {filename_field} for {entry}", fg=WARN_FG)
        elif not dirname:
            typer.secho(f"\tWarning: Missing {dirname} for {entry}", fg=WARN_FG)

    return sort_map


def prompt_select_header(headers: list[str]) -> str:
    """Select a header (column) from a list."""
    while True:
        for i, h in enumerate(headers):
            typer.echo(f"\t[{i}] {h}")
        selection = prompt("Select column:", type=int)

        if selection in range(len(headers)):
            return headers[selection]
        typer.secho("Invalid selection", fg=ERROR_FG)


def prompt_confirm_sort(source: Path, dest: Path, filename_field: str, dir_field: str) -> bool:
    """Prompt user to confirm sorting operation."""
    typer.echo("Please confirm the following:")
    typer.echo(f"\tSource Directory: {source}")
    typer.echo(f"\tUsing for [{filename_field}] to identify files")
    typer.echo(f"\tSorting into folders based on for [{dir_field}] to identify files")
    typer.echo(f"\tDestination Directory: {dest}")

    return confirm("Proceed with sorting?")
