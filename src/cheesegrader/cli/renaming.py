# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond
"""File renaming tool for CheeseGrader CLI.

Replaces Quercus IDs in filenames with student UTORIDs based on a CSV mapping.

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
from cheesegrader.utils import replace_filename_substr

HELP_TEXT = """
Help Menu:
    This tool allows you to rename files in a directory by replacing specified substrings in their filenames.

    You will be prompted to provide:
    - The source directory containing the files to be renamed.
    - A CSV file containing the mapping of current substrings to desired substrings. (If you don't have this, quit and run the 'Downloading' tool first.)
    - The columns in the CSV that correspond to the current substrings and the desired substrings.

    ---
    Enter 'q' or press ctrl+c to quit at any time.
    Enter 'h' for help.
"""

prompt = create_prompt(HELP_TEXT)
confirm = create_confirm(HELP_TEXT)


def run() -> None:
    """Run the renaming workflow."""
    typer.secho("\n=== Renaming TOOL ===\n", bold=True)

    while True:
        # Get source directory
        source_dir = prompt_input_dir(
            "Enter the source directory containing the files to be renamed.",
        )

        # Get map file
        student_data, headers, _ = prompt_get_csv(
            "Enter the path to the .csv file containing the ID -> UTORID mapping.",
        )

        # Select the columns to use
        typer.echo(
            "Select the column containing the IDs CURRENTLY in the filenames.",
        )
        current_id = prompt_select_header(headers)
        headers.remove(current_id)

        typer.echo(
            "Select the column containg the IDs you WANT to be in the filenames."
        )
        desired_id = prompt_select_header(headers)
        rename_map = create_map(student_data, current_id, desired_id)

        # Confirm operation
        if prompt_confirm_rename(source_dir, current_id, desired_id):
            # Perform renaming
            typer.secho("Renaming files...")
            replace_filename_substr(source_dir, rename_map)
            typer.secho("Renaming complete!", fg=SUCCESS_FG)
            return


def create_map(data: list, current_id: str, desired_id: str) -> dict:
    """Create a mapping of filename substrings."""
    sort_map = {}
    for entry in data:
        filename = entry.get(current_id, "").strip()
        dirname = entry.get(desired_id, "").strip()
        if filename and dirname:
            sort_map[filename] = dirname
    return sort_map


def prompt_confirm_rename(
    source: Path, current_id: str, desired_id: str
) -> bool:
    """Prompt user to confirm renaming operation."""
    typer.echo("Please confirm the following:")
    typer.echo(f"\tLooking for files in: {source}")
    typer.echo(f"\tSwapping [{current_id}] with [{desired_id}]")

    return confirm("Is this information correct?")
