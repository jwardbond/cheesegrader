import csv
import os
from pathlib import Path

import typer

from cheesegrader.api_tools import QuercusAssignment, QuercusCourse
from cheesegrader.cli.utils import ERROR_FG, SUCCESS_FG, WARN_FG, create_confirm, create_prompt
from cheesegrader.utils import unzip_dir

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


def run():
    while True:
        typer.secho("\n\n=== DOWNLOAD TOOLS ===", bold=True)

        typer.echo()
        typer.echo("Available downloading modules: ")
        typer.echo("\t[0] Student Lists")
        # typer.echo("\t[1] Student Submissions")

        typer.echo("\t---")
        typer.echo("\t[h] Help")
        typer.echo("\t[q] Quit")

        choice = prompt("What do you want to do?", type=str)

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
    course = prompt_setup_course()
    typer.echo("Enter the output folder for the student list.")
    output_dir = prompt_input_path("Output folder:")
    output_path = output_dir / f"{course.course_id}_student_list.csv"

    typer.secho("Saving student list...")
    course.download_student_list(output_path)
    typer.secho(f"Saved student list to {output_path}", fg=SUCCESS_FG)


def download_submissions() -> None:
    """Download student submissions for an assignment."""
    # Setup course and assignment
    course = prompt_setup_course()
    assignment = prompt_setup_assignment(course)

    # Download submissions zip
    typer.echo("Enter the output path for the submissions zip file (.zip)")
    output_dir = prompt_input_path("Output path:")
    zip_path = output_dir / f"{assignment.assignment_id}_submissions.zip"

    typer.secho("Downloading submissions...")
    assignment.download_submissions_zip(zip_path)
    typer.secho(f"Downloaded submissions to {zip_path}", fg=SUCCESS_FG)

    # Unzip submissions
    typer.secho("Unzipping submissions...")
    unzip_dir(zip_path)
    typer.secho(f"Unzipped submissions to {zip_path / zip_path.stem}", fg=SUCCESS_FG)

    # Replace Canvas IDs with UTORIDs
    typer.secho("Renaming submission files...")
    id_utorid_map = course.get_id_utorid_map()
    assignment.rename_submissions(zip_path.parent / zip_path.stem, id_utorid_map)
    typer.secho("Renamed submission files.", fg=SUCCESS_FG)


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


def prompt_setup_course() -> QuercusCourse:
    """Prompt the user to set up a QuercusCourse object."""
    course_id = prompt("Enter Course ID")
    typer.echo("Loading course...")
    course = QuercusCourse(course_id, token=os.getenv("CG_TOKEN"))
    typer.secho(f"Loaded course: {course.course_name} ({course_id})", fg=SUCCESS_FG)

    return course


def prompt_setup_assignment(course: QuercusCourse) -> QuercusAssignment:
    """Prompt the user to set up a QuercusAssignment object."""
    assignment_id = prompt("Enter Assignment ID")
    typer.echo("Loading assignment...")
    assignment = QuercusAssignment(course.course_id, assignment_id, token=os.getenv("CG_TOKEN"))
    typer.secho(f"Loaded assignment: {assignment.assignment_name} ({assignment_id})", fg=SUCCESS_FG)

    return assignment
