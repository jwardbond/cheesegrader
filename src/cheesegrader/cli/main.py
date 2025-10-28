# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond
"""Main CLI entry point for Cheesegrader."""

import typer

from cheesegrader.cli import (
    copying,
    deleting,
    downloading,
    renaming,
    sorting,
    token,
    uploading,
)
from cheesegrader.cli.utils import create_prompt

app = typer.Typer(help="🧀 Cheesegrader CLI")

HELP_TEXT = """
Help Menu:
    Enter the number corresponding to the module you want to run.

    The first three options are for local file management.
    [0] Sorting: Organizes files into folders based on a student list. Useful for (e.g.) sorting rubrics/assignments by tutorial section.
    [1] Copying: Copies files and names them using a student list. Useful for (e.g.) copying a blank rubric for every student.
    [2] Renaming: Replaces Quercus IDs in filenames with student UTORIDs. Useful when bulk downloading assignments from Quercus.

    The last three options interact with Quercus via the Canvas API.
    [3] Uploading: Uploads grades and/or files to an assignment on Quercus.
    [4] Downloading: Downloads student lists from Quercus.
    [5] Deleting: Deletes comments from an assignment on Quercus.

    ---
    Enter 'q' or press ctrl+c to quit at any time.
    Enter 'h' for help."""


@app.command()
def main() -> None:
    """Main entry point for the Cheesegrader CLI."""
    typer.secho(
        "Welcome to Cheesegrader 🧀! ctrl+c to quit",
        fg=typer.colors.YELLOW,
        bold=True,
    )
    main_menu()


prompt = create_prompt(HELP_TEXT)


def main_menu() -> None:
    """Displays the main menu and handles user input."""
    while True:
        typer.echo()
        typer.echo("Available modules: ")
        typer.echo("    [0] Sorting")
        typer.echo("    [1] Copying")
        typer.echo("    [2] Renaming")
        typer.echo("    [3] Uploading")
        typer.echo("    [4] Downloading")
        typer.echo("    [5] Deleting")
        typer.echo("    ---")
        typer.echo("    [h] Help")
        typer.echo("    [q] Quit")

        choice = prompt("What do you want to do?", type=str)

        match choice:
            case "0":
                sorting.run()
            case "1":
                copying.run()
            case "2":
                renaming.run()
            case "3":
                token.ensure_token()
                uploading.run()
            case "4":
                token.ensure_token()
                downloading.run()
            case "5":
                token.ensure_token()
                deleting.run()
