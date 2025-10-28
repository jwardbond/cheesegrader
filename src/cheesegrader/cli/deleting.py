# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond

"""Comment deleting tool for CheeseGrader CLI."""

import os

import typer

from cheesegrader.api_tools import QuercusAssignment, QuercusCourse, get_user_from_token
from cheesegrader.cli.utils import (
    ERROR_FG,
    SUCCESS_FG,
    create_confirm,
    create_prompt,
    prompt_setup_assignment,
    prompt_setup_course,
)

HELP_TEXT = """
Help Menu:
    This module is for uploading grades and student files to quercus.

    ---
    Enter 'q' or press ctrl+c to quit at any time.
    Enter 'h' for help.
"""

app = typer.Typer(help="Downloading workflow")
prompt = create_prompt(HELP_TEXT)
confirm = create_confirm(HELP_TEXT)


def run() -> None:
    """Run the uploading workflow."""
    typer.secho("\n=== UPLOAD TOOL ===\n", bold=True)

    while True:
        course = prompt_setup_course()
        assignment = prompt_setup_assignment(course)

        typer.echo("Loading comments...")
        authors = assignment.get_comment_authors()
        if not authors:
            typer.secho(
                "No comments found on this assignment. Nothing to delete.",
                fg=ERROR_FG,
            )
            return
        typer.secho("Comments loaded successfully!\n", fg=SUCCESS_FG)

        selected_authors = prompt_select_authors(authors)

        if prompt_confirm_delete(course, assignment, selected_authors):
            typer.echo("Deleting comments...")
            assignment.delete_comments(selected_authors)
            typer.secho("Comments deleted successfully!", fg=SUCCESS_FG)

            return


def prompt_select_authors(authors: dict[int, str]) -> list[dict[int, str]]:
    """Select a header (column) from a list."""
    typer.echo("Select the authors whose comments you want to delete. One at a time.\n")
    add_more = True
    remaining = authors.copy()
    selected = {}
    while add_more:
        typer.echo("Available authors:")
        for i, (_, name) in enumerate(remaining.items()):
            typer.echo(f"    [{i}] {name}")

        selection = prompt("Select author:", type=int)

        # Parse selection
        if 0 <= selection < len(remaining):
            author_id, author_name = list(remaining.items())[selection]
            selected[author_id] = author_name
            remaining.pop(author_id)
            typer.secho(f"Added: {author_name}\n", fg=SUCCESS_FG)
        else:
            typer.secho("Invalid selection.", fg=typer.colors.RED)

        if not remaining or not confirm("Add more authors?"):
            break

    return selected


def prompt_confirm_delete(
    course: QuercusCourse,
    assignment: QuercusAssignment,
    selected_authors: dict,
) -> bool:
    """Display final details before deleting comments."""
    typer.echo("Please confirm the following details before proceeding.\n")

    names = ", ".join(selected_authors.values())

    typer.echo(f"    Deleting comments by: {names}")
    typer.echo(f"    For assignment: {assignment.name}")
    typer.echo(f"    In course: {course.course_name}")

    typer.secho("\nThis action cannot be undone.", bg=ERROR_FG)

    return confirm("Is this information correct?")
