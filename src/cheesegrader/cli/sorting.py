# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond

"""File sorting tool for CheeseGrader CLI.

Sorts files in a source directory into subfolders based on a CSV mapping of
filenames to folder names.

Intended to be run as a subcommand of the Cheesegrader CLI.
"""

from pathlib import Path

import typer

from cheesegrader.cli.utils import (
    SUCCESS_FG,
    WARN_FG,
    create_confirm,
    create_prompt,
    prompt_get_csv,
    prompt_input_dir,
    prompt_select_header,
)
from cheesegrader.utils import sort_files

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
    """Run the sorting workflow."""
    typer.secho("\n=== SORTING TOOL ===\n", bold=True)

    while True:
        # Get source directory
        source_dir = prompt_input_dir(
            "Enter the source directory containing the files to be sorted."
        )

        # Get map file
        student_data, headers, _ = prompt_get_csv(
            "Enter the path to the .csv file containing the filename -> folder mapping.",
        )

        # Select the columns to use
        typer.echo("Select the column to use to identify files:")
        filename_field = prompt_select_header(headers)
        typer.echo("Select the column containing folder names")
        dir_field = prompt_select_header(headers)
        sort_map = create_sort_map(student_data, filename_field, dir_field)

        dest_dir = source_dir.parent / f"{source_dir.name}" / "sorted"

        # Confirm operation
        if prompt_confirm_sort(source_dir, dest_dir, filename_field, dir_field):
            # Perform sorting
            typer.secho("Sorting files...")
            missing = sort_files(source_dir, dest_dir, sort_map)
            typer.secho("Sorting complete!", fg=SUCCESS_FG)

            if missing:
                typer.secho("The following files were not found:", fg=WARN_FG)
                for f in missing:
                    typer.secho(f"    {f}", fg=WARN_FG)

            return


def create_sort_map(data: list, filename_field: str, dir_field: str) -> dict:
    """Create a mapping of filenames to destination directories."""
    sort_map = {}
    for entry in data:
        filename = entry.get(filename_field, "").strip()
        dirname = entry.get(dir_field, "").strip()
        if filename and dirname:
            sort_map[filename] = dirname
        elif not filename:
            typer.secho(f"    Warning: Missing {filename_field} for {entry}", fg=WARN_FG)
        elif not dirname:
            typer.secho(f"    Warning: Missing {dirname} for {entry}", fg=WARN_FG)

    return sort_map


def prompt_confirm_sort(source: Path, dest: Path, filename_field: str, dir_field: str) -> bool:
    """Prompt user to confirm sorting operation."""
    typer.echo("Please confirm the following:")
    typer.echo(f"    Source Directory: {source}")
    typer.echo(f"    Using [{filename_field}] to identify files")
    typer.echo(f"    Sorting into folders based on for [{dir_field}] to identify files")
    typer.echo(f"    Destination Directory: {dest}")

    return confirm("Is this information correct?")
