import csv
import os
from pathlib import Path

import typer

from cheesegrader.api_tools import QuercusAssignment, QuercusCourse
from cheesegrader.cli.utils import ERROR_FG, SUCCESS_FG, WARN_FG, create_confirm, create_prompt
from cheesegrader.utils import UploadMode, upload_files, upload_grades

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


def run() -> None:
    while True:
        # Set up course
        course_id = prompt("Enter Course ID")
        typer.echo("Loading course...")
        course = QuercusCourse(course_id, token=os.getenv("CG_TOKEN"))
        typer.secho(f"Loaded course: {course.course_name} ({course_id})\n", fg=SUCCESS_FG)

        # Set up assignment
        assignment_id = prompt("Enter Assignment ID")
        typer.echo("Loading assignment...")
        assignment = QuercusAssignment(course_id, assignment_id, token=os.getenv("CG_TOKEN"))
        typer.secho(f"Loaded assignment: {assignment.assignment_name} ({assignment_id})\n", fg=SUCCESS_FG)

        # Select mode and upload
        mode = prompt_mode()
        mode = UploadMode(mode)
        upload_errors = []
        match mode:
            case UploadMode.GRADES:
                grades_list, grades_path, header_map = prompt_get_csv({"id", "grade"})
                if prompt_confirm_grade_upload(course, assignment, grades_path, header_map):
                    errors = upload_grades(assignment, grades_list)
                    upload_errors.extend(errors)
                else:
                    continue

            case UploadMode.FILES:
                id_list, id_path, header_map = prompt_get_csv({"id"})
                dir_list = prompt_get_dirs()

                if prompt_confirm_file_upload(course, assignment, id_path, header_map, dir_list):
                    errors = upload_files(assignment, id_list, dir_list)
                    typer.echo()
                else:
                    continue

            case UploadMode.BOTH:
                grades_list, grades_path, header_map = prompt_get_csv({"id", "grade"})
                dir_list = prompt_get_dirs()

                if prompt_confirm_grade_upload(course, assignment, grades_path, header_map):
                    grade_errors = upload_grades(assignment, grades_list)
                    upload_errors.extend(grade_errors)
                    typer.echo()
                else:
                    continue

                if prompt_confirm_file_upload(course, assignment, grades_path, header_map, dir_list):
                    file_errors = upload_files(assignment, grades_list, dir_list)
                    upload_errors.extend(file_errors)
                    typer.echo()
                else:
                    continue

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
    # print(mode)
    return mode


def prompt_get_dirs() -> list[Path]:
    """Prompt user to input directories to search for files.

    Returns:
        list[Path]: A list of directory paths.
    """
    dirs = []
    add_more = True
    while add_more:
        dir_str = prompt("Enter the path to the directory you would like to search for files")
        dir_str = dir_str.strip()
        dir_str = dir_str.strip('"')

        dirs.append(Path(dir_str))

        typer.echo("Added directory: " + dir_str)

        add_more = confirm("Add another directory?", default=False, abort=True)

    return dirs


def prompt_confirm_grade_upload(
    course: QuercusCourse,
    assignment: QuercusAssignment,
    grade_file: Path,
    header_map: list[dict[str, str]],
) -> bool:
    """Display final details before uploading grades."""
    typer.echo("Please confirm the following details before uploading:")
    typer.echo(f"\tCourse:  {course.course_name}")
    typer.echo(f"\tAssigment:  {assignment.assignment_name}")
    typer.echo()
    typer.echo(f"\tGrade file:  {grade_file}")
    typer.echo(f"\t\tID column: {header_map['id']}")
    typer.echo(f"\t\tGrade column: {header_map['grade']}")

    response = confirm("Confirm?")

    return response


def prompt_confirm_file_upload(
    course: QuercusCourse,
    assignment: QuercusAssignment,
    id_file: Path,
    header_map: list[dict[str, str]],
    dirs: list[Path],
) -> bool:
    """Display final details before uploading grades."""
    typer.echo("Please confirm the following details before uploading:")
    typer.echo(f"\tCourse name:  {course.course_name}")
    typer.echo(f"\tAssigmennt name:  Loaded assignment: {assignment.assignment_name}")
    typer.echo(f"\tID file:  {id_file}")
    typer.echo(f"\tID column: {header_map['id']}")
    typer.echo(f"\tLooking for files with {header_map['id']} in name within:")
    for d in dirs:
        typer.echo(f"\t\t{d.absolute()}")

    response = confirm("Confirm?")

    return response


def prompt_select_header(headers: list[str]) -> str:
    """Select a header (column) from a list."""
    while True:
        for i, h in enumerate(headers):
            typer.echo(f"\t[{i}] {h}")
        selection = prompt("Select column:", type=int)

        if selection in range(len(headers)):
            return headers[selection]
        typer.secho("Invalid selection", fg=ERROR_FG)


def prompt_get_csv(required_headers: set[str]) -> tuple[list, Path, dict]:
    """Prompt user to input a CSV file path and returns its contents as a list of dicts.

    If the csv is missing required headers, prompts the user to map existing headers to required ones.

    Args:
        required_headers (set[str]): A set of required column headers.

    Returns:
        grades: list[dict]: A list of {header: value} dicts representing CSV rows.
    """
    while True:
        path_str = prompt("Enter Student List CSV Path")
        path_str = path_str.strip()
        path_str = path_str.strip('"')
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

        # Validate headers and prompt if missing
        header_map = {}
        for required_header in required_headers:
            if required_header not in headers:
                typer.secho(f"CSV is missing required header: {required_header}", fg=WARN_FG)
                typer.secho(f"Please select the column name to use in place of {required_header}:", fg=WARN_FG)
                alternate_header = prompt_select_header(headers)
                header_map[required_header] = alternate_header
            else:
                header_map[required_header] = required_header

        # Clean data to only include required headers
        cleaned_data = []
        for row in data:
            cleaned_row = {required_name: row[csv_name] for required_name, csv_name in header_map.items()}
            cleaned_data.append(cleaned_row)

        return cleaned_data, path, header_map
