from pathlib import Path

import typer

from cheesegrader.api_tools import QuercusAssignment, QuercusCourse
from cheesegrader.cli.utils import (
    ERROR_FG,
    SUCCESS_FG,
    create_confirm,
    create_prompt,
    prompt_input_dir,
    prompt_setup_assignment,
    prompt_setup_course,
)

HELP_TEXT = """
Help Menu:
    This module is for uploading grades and student files to quercus.

    You will need at least:
        - A csv file with an "id" column. These ids should be UTORID
        - The course id
        - The assignment id

    Ids can be found by going on the course website, navigating to the assignment, and looking at the URL:
        https://q.utoronto.ca/courses/[COURSE ID]/assignments/[ASSIGNMENT ID]

    FILE UPLOADING
    Files need to contain UTORIDs in the file names in order to match them to the correct student

    GRADE UPLOADING
    Your .csv file will need to have a "grade" column as well as an "id" column.

    For best results, make sure your csv is clean (no columns with blank headers, no duplicate columns no cells with just spaces, etc.)

    ---
    Enter 'q' or press ctrl+c to quit at any time.
    Enter 'h' for help.
"""

app = typer.Typer(help="Downloading workflows")
prompt = create_prompt(HELP_TEXT)
confirm = create_confirm(HELP_TEXT)


def run() -> None:
    while True:
        typer.secho("\n=== DOWNLOAD TOOLS ===\n", bold=True)

        typer.echo("Available downloading modules: ")
        typer.echo("\t[0] Student Lists")
        typer.echo("\t[1] Student Submissions")

        typer.echo("\t---")
        typer.echo("\t[h] Help")
        typer.echo("\t[q] Quit")

        choice = prompt("What do you want to download?", type=str)

        match choice:
            case "0":
                download_student_list()
                return
            case "1":
                download_submissions()
                return
            case "h":
                continue
            case _:
                typer.secho("Invalid option. Please try again.", fg=ERROR_FG)


def download_student_list() -> None:
    """Download the student list for a course."""
    while True:
        # Setup course
        course = prompt_setup_course()

        # Setup output path
        output_dir = prompt_input_dir("Enter the output directory for the student list.")
        output_path = output_dir / f"{course.course_id}_student_list.csv"

        # Confirm operation
        if prompt_confirm_download_student_list(course, output_path):
            typer.secho("Saving student list...")
            course.download_student_list(output_path)
            typer.secho(f"Saved student list to {output_path}", fg=SUCCESS_FG)
            return


def download_submissions() -> None:
    """Download student submissions for an assignment."""
    while True:
        # Setup course and assignment
        course = prompt_setup_course()
        assignment = prompt_setup_assignment(course)

        # Setup output directory
        output_dir = prompt_input_dir("Enter the output directory for the student submissions.")
        output_dir = output_dir / f"{course.course_id}_{assignment.assignment_id}_submissions"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Confirm operation
        if prompt_confirm_download_submissions(course, assignment, output_dir):
            typer.secho("Downloading submissions...")
            assignment.download_submissions(output_dir)
            typer.secho(f"Downloaded submissions to {output_dir}/submissions", fg=SUCCESS_FG)
            return


def prompt_confirm_download_submissions(course: QuercusCourse, assignment: QuercusAssignment, output_dir: Path) -> bool:
    """Prompt the user to confirm downloading submissions."""
    typer.echo("\nPlease confirm the following information:")
    typer.secho(f"\tCourse: {course.course_name} ({course.course_id})", fg=SUCCESS_FG)
    typer.secho(f"\tAssignment: {assignment.assignment_name} ({assignment.assignment_id})", fg=SUCCESS_FG)
    typer.secho(f"\tOutput Directory: {output_dir}", fg=SUCCESS_FG)

    return confirm("Is this information correct?")


def prompt_confirm_download_student_list(course: QuercusCourse, output_path: Path) -> bool:
    """Prompt the user to confirm downloading the student list."""
    typer.echo("\nPlease confirm the following information:")
    typer.secho(f"\tCourse: {course.course_name} ({course.course_id})", fg=SUCCESS_FG)
    typer.secho(f"\tOutput File: {output_path}", fg=SUCCESS_FG)

    return confirm("Is this information correct?")
