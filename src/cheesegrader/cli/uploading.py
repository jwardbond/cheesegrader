from enum import Enum
from pathlib import Path

import typer

from cheesegrader.api_tools import QuercusAssignment, QuercusCourse
from cheesegrader.cli.utils import (
    SUCCESS_FG,
    create_confirm,
    create_prompt,
    prompt_get_csv,
    prompt_select_header,
    prompt_setup_assignment,
    prompt_setup_course,
)
from cheesegrader.utils import search_dirs

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

app = typer.Typer(help="Uploading workflow")
prompt = create_prompt(HELP_TEXT)
confirm = create_confirm(HELP_TEXT)


class UploadMode(Enum):
    """Defines the allowed modes for the upload workflow."""

    GRADES = 0
    FILES = 1
    BOTH = 2


def run() -> None:
    typer.secho("\n=== UPLOAD TOOL ===\n", bold=True)

    while True:
        course = prompt_setup_course()
        assignment = prompt_setup_assignment(course)

        # Select mode and upload
        mode = UploadMode(prompt_mode())

        # Get student file
        data, headers, csv_path = prompt_get_csv("Enter the path to the student list .csv file.")

        # Get utorid column
        typer.echo("Select which column contains the UTORID")
        id_col = prompt_select_header(headers)

        need_grades = mode in (UploadMode.GRADES, UploadMode.BOTH)
        need_files = mode in (UploadMode.FILES, UploadMode.BOTH)

        if need_grades:
            typer.echo("Select which column contains the grades.")
            grade_col = prompt_select_header(headers)
            grades = {data[id_col]: float(data[grade_col]) for data in data}
        else:
            grade_col = None

        if need_files:
            dir_list = prompt_get_dirs()
            filepaths = {d[id_col]: search_dirs(dir_list, d[id_col]) for d in data}
        else:
            dir_list = None

        # Confirm and upload
        if prompt_confirm_upload(
            course,
            assignment,
            mode,
            csv_path,
            id_col,
            grade_col,
            dir_list,
        ):
            if need_grades:
                typer.echo("Uploading grades...")
                upload_errors = assignment.bulk_upload_grades(grades)
                typer.secho("Grade upload complete!", fg=SUCCESS_FG)
            if need_files:
                typer.echo("Uploading files...")
                upload_errors = assignment.bulk_upload_files(filepaths)
                typer.secho("File upload complete!", fg=SUCCESS_FG)

            # Print upload errors
            if upload_errors:
                typer.echo("The following uploads failed:")
                for emsg in upload_errors:
                    typer.echo(emsg)

            return


def prompt_mode() -> str:
    """Prompt user to select an upload mode."""
    typer.echo("Available upload modes: ")
    typer.echo("\t[0] Grades only")
    typer.echo("\t[1] Files only")
    typer.echo("\t[2] Both Grades and Files")

    mode = prompt("Select upload mode", type=int)

    return mode


def prompt_get_dirs() -> list[Path]:
    """Prompt user to input directories to search for files.

    Args:
        prompt_text (str): The prompt text to display to the user.

    Returns:
        list[Path]: A list of directory paths.
    """
    dirs = []
    add_more = True
    typer.echo("Enter the directories to search for student files. One at a time.")

    while add_more:
        dir_str = prompt("Enter path to directory.").strip().strip('"')
        dirs.append(Path(dir_str))

        typer.secho(f"Added directory: {dir_str}", fg=SUCCESS_FG)

        add_more = confirm("Add another directory?")

    return dirs


def prompt_confirm_upload(
    course: QuercusCourse,
    assignment: QuercusAssignment,
    mode: UploadMode,
    csv_path: Path,
    id_col: str,
    grade_col: str | None,
    dir_list: list[Path] | None,
) -> bool:
    """Display final details before uploading."""
    typer.echo("Please confirm the following details before uploading:")
    typer.echo(f"\tCourse: {course.course_name}")
    typer.echo(f"\tAssignment: {assignment.assignment_name}")
    typer.echo(f"\tUpload mode: {mode.name}")
    typer.echo(f"\tStudent file: {csv_path}")
    typer.echo(f"\tID column: {id_col}")
    if grade_col:
        typer.echo(f"\tGrade column: {grade_col}")
    if dir_list:
        typer.echo(f"\tDirectories to search: {', '.join(str(d) for d in dir_list)}")

    return confirm("Is this information correct?")
