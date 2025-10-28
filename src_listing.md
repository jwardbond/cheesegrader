``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\__init__.py

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\__main__.py
from cheesegrader.cli.main import app

if __name__ == "__main__":
    app()

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\api_tools\__init__.py
from cheesegrader.api_tools.assignments import QuercusAssignment
from cheesegrader.api_tools.courses import QuercusCourse
from cheesegrader.api_tools.tokens import validate_token

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\api_tools\assignments.py
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond
"""Quercus Assignment API Client.

This module provides the QuercusAssignment class for interacting with the
Canvas/Quercus LMS API, specifically for managing assignments, submissions,
grades, and file uploads.

TODO list:
    * Implement batch submission/grade updates.
    * Implement deletion of submission comments.
    * Handle group assignments.

Classes:
    QuercusAssignment: The primary client class for assignment management.
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests as r
from tqdm import tqdm

from cheesegrader.api_tools.courses import QuercusCourse
from cheesegrader.utils import download_file


class QuercusAssignment:
    """A class to interact with the Quercus API for uploading and managing course assignments.

    This class provides methods for accessing assignment details, and uploading grades/rubrics.

    Attributes:
        course_id (str, int): The course number on Quercus
        token (str): The raw authentication token.
        auth_key (dict): The Authorization header dictionary for Canvas API requests. i.e. {'Authorization': 'Bearer <token>'}
        endpoints (dict): A collection of API endpoint URLs related to the assignment.
        assignment (dict): The assignment information fetched from the API.
        group_ids (list): A list of group IDs associated with the course.
    """

    def __init__(self, course_id: int, assignment_id: int, token: str) -> None:
        """Initializes the QuercusAssignment object and fetches initial data.

        Args:
            course_id (int): The course ID number on Quercus.
            assignment_id (int): The assignment ID number on Quercus.
            token (str): The raw authentication token (string). Details about this are in the README.
        """
        self.course_id = course_id
        self.assignment_id = assignment_id
        self.token = token
        self.auth_key = {"Authorization": f"Bearer {token}"}
        self.endpoints = {
            "course": f"https://q.utoronto.ca/api/v1/courses/{course_id}/",
            "assignment": f"https://q.utoronto.ca/api/v1/courses/{course_id}/assignments/{assignment_id}",
            "submissions": f"https://q.utoronto.ca/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions?per_page=100",
            "submission": f"https://q.utoronto.ca/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/sis_user_id:",
            "submission_comments_suffix": "/comments/files",
            "groups": "https://q.utoronto.ca/api/v1/group_categories/",
            "groups_suffix": "/groups",
            "group_users": "https://q.utoronto.ca/api/v1/groups/",
            "group_users_suffix": "/users",
        }
        # self.group_ids = self._get_groups() # TODO

    @property
    def assignment(self) -> dict:
        """Returns the assignment information."""
        if not hasattr(self, "_assignment"):
            url = self.endpoints["assignment"]
            response = r.get(url, headers=self.auth_key, timeout=10).json()
            self._assignment = response
        return self._assignment

    @property
    def assignment_name(self) -> str:
        """Returns the name of the assignment."""
        return self.assignment["name"]

    @property
    def is_group(self) -> bool:
        """Returns whether the assignment is a group assignment."""
        return self.assignment["group_category_id"] is not None

    @property
    def course(self) -> QuercusCourse:
        """Returns the QuercusCourse object for the assignment's course."""
        if not hasattr(self, "_course"):
            self._course = QuercusCourse(self.course_id, token=self.token)
        return self._course

    def download_submissions(self, destination: Path) -> None:
        """Downloads the submissions zip file for the assignment.

        Args:
            destination (Path): The path where the zip file will be saved.
        """
        url = self.endpoints["submissions"]
        response = r.get(url, headers=self.auth_key, timeout=10)
        destination.mkdir(parents=True, exist_ok=True)

        # Ensure filenames contain utorid
        id_utorid_map = self.course.get_id_utorid_map()

        # Loop through api pages and construct submissions list
        submissions = []
        while "next" in response.links:
            # Get list of file urls and desired filepaths
            for submission in response.json():
                for attachment in submission.get("attachments", []):
                    url = attachment["url"]

                    user_id = str(submission["user_id"])
                    utorid = str(id_utorid_map.get(user_id, user_id))

                    filename = utorid + "_" + attachment["display_name"]

                    # Because students insert crazy symbols in filenames
                    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", filename).strip().rstrip(". ")
                    filepath = destination / filename

                    submissions.append({"path": filepath, "url": url})
            response = r.get(response.links["next"]["url"], headers=self.auth_key, timeout=10)

        # Download the files to the output directory
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(download_file, sub["url"], sub["path"]) for sub in submissions]
            for future in tqdm(as_completed(futures), total=len(futures)):
                future.result()

    def group_data_parser(self, group_info: dict) -> list:
        """Given group info (ID, grade), returns individual student info (sis_id, group grade).

        Fetches the list of students belonging to a group ID to apply a group grade to each individual student's SIS ID.

        Args:
            group_info: A dictionary containing the group's ID (name) and the grade
                        to be applied, e.g., {'id': 'Group A', 'grade': 90.0}.

        Returns:
            list: A list of dictionaries, each containing student grading information
        """
        url = (
            self.endpoints["group_users"] + str(self.group_ids[group_info["id"]]) + self.endpoints["group_users_suffix"]
        )
        params = {"per_page": 20}

        response = r.get(url, params=params, headers=self.auth_key, timeout=10)

        parsed_data = []

        for user in response.json():
            parsed_data.append(
                {
                    "id": user["sis_user_id"],
                    "grade": group_info["grade"],
                    "group_id": group_info["id"],
                },
            )

        return parsed_data

    def post_grade(self, sis_id: str, grade: float) -> bool:
        """Posts the grade for a given user.

        The ids must be the sis_user_id for the user. For UofT this is their UTORid.

        Args:
            sis_id: The Quercus sis_id for the user. For UofT this is the same as their UTORid.
            grade: The grade (float) to be posted for the user.

        Returns:
            bool: True if the request was successful (HTTP status 2xx), False otherwise.
        """
        url = self.endpoints["submission"] + f"{sis_id}"
        grade_info = {"submission[posted_grade]": f"{grade:.1f}"}
        response = r.put(url, data=grade_info, headers=self.auth_key, timeout=10)

        return response.ok

    def upload_file(self, sis_id: int, filepath: Path) -> None:
        """Uploads a single file for a given user.

        The ids must be the sis_user_id for the user. For UofT this is their UTORid.

        Api docs for uploading a file: https://developerdocs.instructure.com/services/canvas/basics/file.file_uploads
        Api docs for attaching uploaded file to comment: https://developerdocs.instructure.com/services/canvas/resources/submissions#method.submissions_api.create_file

        Args:
            sis_id (int): Quercus sis_id for the user. For UofT this is the same as their UTORid.
            filepath (Path): Path to the file to be uploaded
        Returns:
            bool: True if the final linkig was successful (HTTP status 2xx), False otherwise.
        """
        url = self.endpoints["submission"] + f"{sis_id}" + self.endpoints["submission_comments_suffix"]

        # Step 1: Get upload URL
        name = filepath.name
        size = filepath.stat().st_size
        file_info = {"name": name, "size": size}
        response = r.post(
            url,
            data=file_info,
            headers=self.auth_key,
            timeout=10,
        )

        # Step 2: Upload file
        upload_url = response.json()["upload_url"]
        file_data = {"upload_file": filepath.open("rb")}
        upload_params = response.json()["upload_params"]
        response = r.post(
            upload_url,
            files=file_data,
            data=upload_params,
            timeout=10,
        )

        # Step 3: Link uploaded file id as a submission comment
        file_id = response.json()["id"]
        submission_url = self.endpoints["submission"] + f"{sis_id}"
        comment_info = {
            "comment[file_ids]": [file_id],
            "comment[group_comment]": "true",
        }
        response = r.put(
            submission_url,
            data=comment_info,
            headers=self.auth_key,
            timeout=10,
        )

        return response.ok

    def bulk_upload_grades(self, grades: dict[str, float]) -> list[str]:
        """Posts grades to Quercus for the given students.

        Args:
            grades (dict[str, float]): A dictionary mapping SIS IDs (str) to grades (float).
                SIS IDs are typically UTORids for UofT students.

        Returns:
            list[str]: A list of error messages for grades that failed to upload.
        """
        error_list = []
        for utorid, grade in tqdm(grades.items()):
            if not grade:
                error_list.append(f"{utorid}: \t Missing grade")
                continue

            try:
                self.post_grade(utorid, grade)
            except Exception:  # noqa: BLE001
                error_list.append(f"{utorid}: \t Missing student or post failed")

        return error_list

    def bulk_upload_files(
        self,
        student_files: dict[str, list[Path]],
    ) -> list[str]:
        """Finds files for the given IDs in the specified directories and uploads them as submissions.

        Args:
            student_files (dict): A dictionary mapping SIS IDs (str) to lists of file paths (Path).
                SIS IDs are typically UTORids for UofT students.

        Returns:
            list[str]: A list of error messages for files that were not found or failed to upload.
        """
        error_list = []
        for student, files in tqdm(student_files.items()):
            if not files:
                error_list.append(f"{student}: \t No files found for upload")
                continue

            for file in files:
                try:
                    self.upload_file(student, file)
                except Exception:  # noqa: BLE001
                    error_list.append(f"{student}: \t Upload failed for {file.name}")

        return error_list

    # def _get_groups(self) -> dict | None:
    #     if self.is_group:
    #         url = self.endpoints["groups"] + str(self.assignment["group_category_id"]) + self.endpoints["groups_suffix"]

    #         data = {"include": ["users"]}
    #         params = {"per_page": 200}

    #         response = r.get(url, params=params, data=data, headers=self.auth_key, timeout=10)

    #         group_data = response.json()

    #         group_ids = {}

    #         if len(group_data) > 0:
    #             for group in group_data:
    #                 group_ids[group["name"]] = group["id"]

    #         links = response.headers["Link"].split(",")

    #         while len(links) > 1 and "next" in links[1]:
    #             next_url = links[1].split("<")[1].split(">")[0].strip()
    #             response = r.get(next_url, headers=self.auth_key, timeout=10)

    #             group_data = response.json()

    #             if len(group_data) > 0:
    #                 for group in group_data:
    #                     group_ids[group["name"]] = group["id"]

    #             links = response.headers["Link"].split(",")

    #         return group_ids

    #     return None

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\api_tools\courses.py
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond
"""Quercus Course API Client.

This module provides the QuercusCourse class for interacting with the
Canvas/Quercus LMS API. Mainly useful for fetching student lists.

Classes:
    QuercusCourse: The primary client class for course management.
"""

import csv
from pathlib import Path

import requests as r


class QuercusCourse:
    """A course object for interacting with a Quercus course through Canvas APIs.

    This class provides methods for accessing course details, student lists, and student submissions.

    Attributes:
        course_id (str, int): The course number on Quercus
        auth_key (dict): The Authorization header dictionary for Canvas API requests. i.e. {'Authorization': 'Bearer <token>'}
        endpoints (dict): A collection of API endpoint URLs related to the course.
        course (dict): The course information fetched from the API.
        students (list): A list of dictionary records for students enrolled in the course.
    """

    def __init__(self, course_id: str | int, token: str) -> None:
        """Initializes the QuercusCourse object and fetches course and student data.

        Args:
            course_id: The course ID number on Quercus.
            token: The raw authentication token (string).
        """
        self.course_id = course_id
        self.auth_key = {"Authorization": f"Bearer {token}"}

        self.endpoints = {
            "course": f"https://q.utoronto.ca/api/v1/courses/{course_id}/",
            "students": f"https://q.utoronto.ca/api/v1/courses/{course_id}/students",
        }

    @property
    def course_name(self) -> str:
        """Returns the name of the course."""
        return self.course["name"]

    @property
    def students(self) -> list[dict]:
        """Returns the list of students enrolled in the course."""
        if not hasattr(self, "_students"):
            url = self.endpoints["students"]
            response = r.get(url, headers=self.auth_key, timeout=10)
            self._students = remove_duplicates(response.json())
        return self._students

    @property
    def course(self) -> dict:
        """Returns the course information."""
        if not hasattr(self, "_course"):
            url = self.endpoints["course"]
            response = r.get(url, headers=self.auth_key, timeout=10)
            self._course = response.json()
        return self._course

    def download_student_list(self, destination: Path) -> None:
        """Generates and saves a dataframe of student information for the course.

        Attributes:
            destination (Path): The file path where the student list CSV will be saved.
        """
        fields = ["sis_user_id", "id", "integration_id", "name", "sortable_name"]

        rows = []
        for s in self.students:
            row = {k: s.get(k, "") for k in fields}

            if ", " in row["sortable_name"]:
                row["lname"], row["fname"] = row["sortable_name"].split(", ")

            row["utorid"] = s.get("sis_user_id", "")
            rows.append(row)

        # Write to csv
        fields = [*fields, "fname", "lname", "utorid"]
        with destination.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def get_id_utorid_map(self) -> dict[str, str]:
        """Returns a mapping of student Canvas IDs to UtorIDs."""
        id_utorid_map = {}
        for s in self.students:
            canvas_id = str(s.get("id", ""))
            utorid = s.get("sis_user_id", "")
            id_utorid_map[canvas_id] = utorid

        return id_utorid_map


def remove_duplicates(data: list[dict]) -> list[dict]:
    """Removes duplicate student entries based on their Canvas ID."""
    seen_ids = set()
    unique_data = []
    for entry in data:
        canvas_id = entry.get("id")
        if canvas_id not in seen_ids:
            seen_ids.add(canvas_id)
            unique_data.append(entry)
    return unique_data

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\api_tools\tokens.py
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond
"""Quercus Token API Tools.

This module provides functions for validating and managing authentication tokens
for accessing the Canvas/Quercus LMS API.

Functions:
    validate_token: Validates a given authentication token.
"""

import requests as r

CANVAS_API_BASE = "https://canvas.instructure.com/api/v1"


def validate_token(token: str) -> bool:
    """Return True if the token is valid, False otherwise."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = r.get(f"{CANVAS_API_BASE}/courses", headers=headers, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"Token validation failed: {response.status_code} {response.text}")
            return False
    except r.RequestException as e:
        print(f"Error validating token: {e}")
        return False

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\cli\__init__.py

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\cli\copying.py
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond

"""File copying and renaming tool for CheeseGrader CLI.

Guides the user through copying a file multiple times and renaming
each copy based on a provided CSV file containing student information.

Intended to be run as a subcommand of the Cheesegrader CLI.
"""

from pathlib import Path

import typer

from cheesegrader.cli.utils import (
    ERROR_FG,
    SUCCESS_FG,
    WARN_FG,
    create_confirm,
    create_prompt,
    prompt_get_csv,
    prompt_input_dir,
    prompt_select_header,
)
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
    """Run the copying workflow."""
    typer.secho("\n=== COPY TOOL ===\n", bold=True)

    input_filepath = prompt_input_filepath("Enter the path to the file to be copied.")

    # Load student list
    student_data, headers, csv_path = prompt_get_csv("Enter the path to the student list .csv file.")

    # Select which columns to use when creating name
    name_fields = prompt_select_headers(headers)

    # Get destination path
    dest_dir = prompt_input_dir("Input the destination folder")

    if prompt_confirm_copy(input_filepath, dest_dir, csv_path, name_fields):
        # Copy folders
        typer.secho("Copying files...", fg=WARN_FG)
        copy_rename(input_filepath, student_data, name_fields, dest_dir)
        typer.secho("Files copied", fg=SUCCESS_FG)

        return


def prompt_input_filepath(prompt_text: str) -> Path:
    """Prompt the user for a path to a file and validate that it exists."""
    while True:
        typer.echo(prompt_text)
        path_str = prompt("Filepath").strip().strip('"')
        path = Path(path_str).resolve()
        if path.exists():
            return path
        typer.secho(f"File not found at {path.resolve()}! Try again.", fg=ERROR_FG)


def prompt_select_headers(headers: list[str]) -> list[str]:
    """Let the user select multiple headers from the list using prompt_select_header."""
    selected = []
    remaining = list(headers)

    typer.secho("Select columns to use when renaming files (pick one at a time)")
    typer.secho("Whatever is in these columns will be PREPENDED to the file name.")

    while remaining:
        header = prompt_select_header(remaining)
        selected.append(header)
        remaining.remove(header)

        if not remaining:
            break
        if not confirm("Select another column?"):
            break

    return selected


def prompt_confirm_copy(
    input_filepath: Path,
    dest_dir: Path,
    csv_path: Path,
    name_fields: list[str],
) -> bool:
    """Prompt the user to confirm proceeding with the copy operation."""
    typer.echo("Please confirm the following settings:")
    typer.echo(f"\tInput file to copy: {input_filepath}")
    typer.echo(f"\tDestination directory: {dest_dir}")
    typer.echo(f"\tCSV being used for renaming: {csv_path}")

    # Construct sample filename
    base = input_filepath.stem
    suffix = input_filepath.suffix
    filename = [f"[{field}]" for field in name_fields]
    filename = "_".join(filename)
    filename = filename + "_" + base + suffix
    filename = filename.replace(" ", "_")  # remove any lingering spaces
    filename = filename.lower()
    typer.echo(f"\tFile name example: {filename}")

    return confirm("Is this information correct?")

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\cli\downloading.py
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond

"""Download tools for Quercus course data.

This module provides CLI workflows for downloading student lists and
assignment submissions from Quercus using the Canvas API. It supports:
    • Downloading enrolled student lists as CSV files.
    • Downloading student submissions (PDFs, Word docs, etc.) for assignments.

Users are prompted for course and assignment IDs, output directories,
and confirmation before any downloads occur.

Intended to be run as a subcommand of the Cheesegrader CLI.
"""

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
    """Run the downloading workflow."""
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

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\cli\main.py
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond
"""Main CLI entry point for Cheesegrader."""

import typer

from cheesegrader.cli import copying, downloading, sorting, token, uploading
from cheesegrader.cli.utils import create_prompt

app = typer.Typer(help="🧀 Cheesegrader CLI")

HELP_TEXT = """
Help Menu:
    Enter the number corresponding to the module you want to run.
    [0] Sorting: Organizes files into folders based on a student list. Useful for (e.g.) sorting rubrics/assignments by tutorial section.
    [1] Copying: Copies files and names them using a student list. Useful for (e.g.) copying a blank rubric for every student.
    [2] Uploading: Uploads grades and/or files to an assignment on Quercus.
    [3] Downloading: Downloads student lists from Quercus.

    ---
    Enter 'q' or press ctrl+c to quit at any time.
    Enter 'h' for help."""


@app.command()
def main() -> None:
    """Main entry point for the Cheesegrader CLI."""
    typer.secho(
        "Welcome to 🧀 Cheesegrader! ctrl+c to quit",
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
        typer.echo("\t[0] Sorting")
        typer.echo("\t[1] Copying")
        typer.echo("\t[2] Uploading")
        typer.echo("\t[3] Downloading")
        typer.echo("\t---")
        typer.echo("\t[h] Help")
        typer.echo("\t[q] Quit")

        choice = prompt("What do you want to do?", type=str)

        match choice:
            case "0":
                sorting.run()
            case "1":
                copying.run()
            case "2":
                token.ensure_token()
                uploading.run()
            case "3":
                token.ensure_token()
                downloading.run()

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\cli\sorting.py
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
        source_dir = prompt_input_dir("Enter the source directory containing the files to be sorted.")

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
                    typer.secho(f"\t{f}", fg=WARN_FG)

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
            typer.secho(f"\tWarning: Missing {filename_field} for {entry}", fg=WARN_FG)
        elif not dirname:
            typer.secho(f"\tWarning: Missing {dirname} for {entry}", fg=WARN_FG)

    return sort_map


def prompt_confirm_sort(source: Path, dest: Path, filename_field: str, dir_field: str) -> bool:
    """Prompt user to confirm sorting operation."""
    typer.echo("Please confirm the following:")
    typer.echo(f"\tSource Directory: {source}")
    typer.echo(f"\tUsing [{filename_field}] to identify files")
    typer.echo(f"\tSorting into folders based on for [{dir_field}] to identify files")
    typer.echo(f"\tDestination Directory: {dest}")

    return confirm("Is this information correct?")

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\cli\token.py
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond

"""Token management utilities for Cheesegrader CLI.

This module provides functions to:
    - Ensure a valid API token is available (`ensure_token`)
    - Load a token from disk (`load_token`)
    - Save a token to disk (`save_token`)
    - Delete a saved token (`delete_token`)

Tokens are persisted in the user's home directory at:
    ~/.cheesegrader_token

The module also interacts with the environment variable:
    CG_TOKEN

Intended to be run before other CLI subcommands to ensure authentication.
"""

import json
import os
from pathlib import Path

import typer

from cheesegrader.api_tools import validate_token
from cheesegrader.cli.utils import SUCCESS_FG, create_confirm, create_prompt

TOKEN_FILE = Path.home() / ".cheesegrader_token"
TOKEN_VAR_NAME = "CG_TOKEN"  # noqa: S105

HELP_MSG = """
Help Menu:
    This module manages the API token required for authenticating with the Canvas API.

    Tokens can be generated by going to https://q.utoronto.ca/profile/settings and generating
    a new access token.

    You can choose to save your token locally for convenience, or enter it each time.

    The token is stored in a file at ~/.cheesegrader_token and loaded into the
    environment variable CG_TOKEN for use by other CLI commands.

    This program does not share or transmit your token beyond validating it with the Canvas API.

    ---
    Enter 'q' or press ctrl+c to quit at any time.
    Enter 'h' for help.

"""

prompt = create_prompt(HELP_MSG)
confirm = create_confirm(HELP_MSG)


def ensure_token() -> str:
    """Prompt for token if not stored, validate, and persist."""
    use_saved = False
    token = None

    if TOKEN_FILE.exists():
        typer.echo(f"A saved token was found at {TOKEN_FILE}.")
        use_saved = confirm("Use saved token?")

        token = load_token() if use_saved else None

    if not token:
        typer.echo("No saved token found.")
        token = typer.prompt("Enter your API token")

    typer.echo("Validating token...")
    if not validate_token(token):
        typer.secho("Invalid token.", fg=typer.colors.RED)
        typer.echo(
            "You can get a token from your account page by following the instructions: https://developerdocs.instructure.com/services/canvas/oauth2/file.oauth#manual-token-generation",
        )
        return ensure_token()

    typer.secho("Token validated.", fg=typer.colors.GREEN)

    if not use_saved:
        save_new = confirm("Do you want to save this token for future use?", default=True)
        if save_new:
            save_token(token)

    # Load into env
    os.environ[TOKEN_VAR_NAME] = token
    return None


def load_token() -> str | None:
    """Load the token from a token file."""
    if TOKEN_FILE.exists():
        try:
            return json.loads(TOKEN_FILE.read_text()).get("token")
        except json.JSONDecodeError:
            return None
    return None


def save_token(token: str) -> None:
    """Save the token to a token file."""
    typer.secho(f"Saved token to {TOKEN_FILE}", fg=SUCCESS_FG)
    TOKEN_FILE.write_text(json.dumps({"token": token}))


def delete_token() -> None:
    """Delete the saved token file."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\cli\uploading.py
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond

"""File uploading tool for CheeseGrader CLI.

Guides the user through uploading grades and student files to Quercus.

Interacts with CANVAS/Quercus APIs to upload grades and student files
based on a provided CSV file containing student UTORIDs.

Intended to be run as a subcommand of the Cheesegrader CLI.
"""

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
    """Run the uploading workflow."""
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

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\cli\utils.py
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond

"""CLI prompt utilities for CheeseGrader.

This module provides reusable prompt and confirmation functions with built-in
help messages and quit options. It includes utilities for:

    - Prompting for and validating CSV files and directories
    - Selecting columns from CSV headers
    - Setting up Quercus courses and assignments
    - Ensuring consistent CLI formatting and feedback with colors

All prompts support entering 'h' for help or 'q' to quit.
"""

import csv
import os
import textwrap
from collections.abc import Callable
from pathlib import Path

import typer

from cheesegrader.api_tools import QuercusAssignment, QuercusCourse

HELP_REGISTRY = {}
DEFAULT_HELP_MSG = "Enter 'q' or press ctrl+c to quit at any time.\nEnter 'h' for help."

# Prompt styles
PROMPT_BG = typer.colors.YELLOW
PROMPT_FG = typer.colors.BLACK

# Help message styles
HELP_FG = typer.colors.CYAN
HELP_BG = typer.colors.CYAN

# General styles
ERROR_FG = typer.colors.RED
SUCCESS_FG = typer.colors.GREEN
WARN_FG = typer.colors.YELLOW


def create_prompt(help_msg: str) -> Callable[..., str]:
    """Creates a function to replace typer.prompt.

    Adds a help message and the option to enter 'q' to quit.
    """

    def patched_prompt(*args, **kwargs) -> str:  # noqa: ANN002, ANN003
        prompt_text = args[0] if args else kwargs.get("text", "")

        # Remove text from args so not duplicated
        if args:
            args = args[1:]

        while True:
            typer.echo()
            typer.secho(prompt_text, fg=PROMPT_FG, bg=PROMPT_BG, nl=False)

            response = typer.prompt("", *args, **kwargs)
            typer.echo()

            # Loop if user enters help
            if response in ("h", "H"):
                typer.secho(help_msg, fg=HELP_FG)
                typer.echo()
                typer.secho("Press any key to continue", fg=PROMPT_FG, bg=HELP_BG, nl=False)
                input()
            elif response in ("q", "Q"):
                raise typer.Exit
            else:
                return response

    return patched_prompt


def create_confirm(help_msg: str) -> Callable[..., str]:
    """Creates a function to replace typer.confirm.

    Adds a help message and the option to enter 'q' to quit.
    """

    def patched_confirm(*args, **kwargs) -> str:  # noqa: ANN002, ANN003
        while True:
            prompt_text = args[0] if args else kwargs.get("text", "")
            typer.echo()
            typer.secho(prompt_text + " [y/n]", fg=PROMPT_FG, bg=PROMPT_BG, nl=False)

            # Remove text from args so not duplicated
            if args:
                args = args[1:]

            response = typer.prompt("", *args, **kwargs).strip().lower()
            typer.echo()

            if response == "h":
                typer.secho(help_msg, fg=HELP_FG)
                typer.echo()
                typer.secho("Press any key to continue", fg=PROMPT_FG, bg=HELP_BG, nl=False)
                input()
            elif response == "q":
                typer.Exit()
            elif response in ("y", "yes"):
                return True
            elif response in ("n", "no"):
                return False
            else:
                typer.secho("Invalid input. Enter 'y', 'n', or 'h'.", fg=ERROR_FG)

    return patched_confirm


def prompt_get_csv(prompt_text: str) -> tuple[list, Path, dict]:
    """Prompt user to input a CSV file path and returns its contents as a list of dicts."""
    help_msg = """
    Help Menu:
        Enter the full path to the CSV file.

        ---
        Enter 'q' or press ctrl+c to quit at any time.
        Enter 'h' for help.
    """
    prompt = create_prompt(help_msg)

    while True:
        typer.echo(prompt_text)
        path_str = prompt("CSV path").strip().strip('"')
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

        return data, headers, path


def prompt_select_header(headers: list[str]) -> str:
    """Select a header (column) from a list."""
    help_msg = textwrap.dedent("""
    Help Menu:
        Enter the number corresponding to the column you want to select.

        ---
        Enter 'q' or press ctrl+c to quit at any time.
        Enter 'h' for help.
    """)
    prompt = create_prompt(help_msg)

    while True:
        for i, h in enumerate(headers):
            typer.echo(f"\t[{i}] {h}")
        selection = prompt("Select column:", type=int)

        if selection in range(len(headers)):
            return headers[selection]
        typer.secho("Invalid selection", fg=ERROR_FG)


def prompt_input_dir(prompt_text: str) -> Path:
    """Prompt the user for a path to a directory and validate that it exists."""
    help_msg = textwrap.dedent("""
    Help Menu:
        Enter the full path to the desired directory.

        ---
        Enter 'q' or press ctrl+c to quit at any time.
        Enter 'h' for help.
    """)
    prompt = create_prompt(help_msg)

    while True:
        typer.echo(prompt_text)
        path_str = prompt("Directory path").strip().strip('"')
        path = Path(path_str).resolve()
        if path.exists():
            return path

        typer.secho("Directory does not exist!", fg=WARN_FG)
        typer.secho("Creating directory...", fg=WARN_FG)
        path.mkdir(parents=True, exist_ok=True)
        typer.secho(f"Created directory at {path}", fg=SUCCESS_FG)
        return path


def prompt_setup_course() -> QuercusCourse:
    """Prompt the user to set up a QuercusCourse object."""
    help_msg = textwrap.dedent("""
    Help Menu:
        Enter the Course ID for the Quercus course you want to set up.

        The easiest way to find this is to log into Quercus, navigate to the course, and look at the URL.

        ---
        Enter 'q' or press ctrl+c to quit at any time.
        Enter 'h' for help.
    """)
    prompt = create_prompt(help_msg)

    typer.echo("Enter The Course ID.")
    course_id = prompt("Course ID")
    typer.echo("Loading course...")
    course = QuercusCourse(course_id, token=os.getenv("CG_TOKEN"))
    typer.secho(f"Loaded course: {course.course_name} ({course_id})\n", fg=SUCCESS_FG)

    return course


def prompt_setup_assignment(course: QuercusCourse) -> QuercusAssignment:
    """Prompt the user to set up a QuercusAssignment object."""
    help_msg = textwrap.dedent("""
    Help Menu:
        Enter the Assignment ID for the Quercus assignment you want to set up.

        The easiest way to find this is to log into Quercus, navigate to the assignment, and look at the URL.

        ---
        Enter 'q' or press ctrl+c to quit at any time.
        Enter 'h' for help.
    """)
    prompt = create_prompt(help_msg)

    typer.echo("Enter the Assignment ID.")
    assignment_id = prompt("Assignment ID")
    typer.echo("Loading assignment...")
    assignment = QuercusAssignment(course.course_id, assignment_id, token=os.getenv("CG_TOKEN"))
    typer.secho(f"Loaded assignment: {assignment.assignment_name} ({assignment_id})\n", fg=SUCCESS_FG)

    return assignment

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\utils\__init__.py
from cheesegrader.utils.file_utils import (
    copy_rename,
    download_file,
    replace_filename_substr,
    search_dirs,
    sort_files,
    unzip_dir,
)

__all__ = [
    "copy_rename",
    "download_file",
    "replace_filename_substr",
    "search_dirs",
    "sort_files",
    "unzip_dir",
]

``
``python
// filepath: E:\OneDrive\Projects\programming\cheesegrader\src\cheesegrader\utils\file_utils.py
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond
"""Utility functions for file operations in Cheesegrader."""

import shutil
import zipfile
from pathlib import Path

import requests as r


def copy_rename(
    input_filepath: Path,
    student_list: list[dict],
    name_fields: list[str],
    output_dir: Path,
) -> None:
    """Copies a file and renames it according to user-specified columns in a class .csv file.

    This function reads a CSV file containing student information, and for each student,
    it copies a specified input file to a designated output directory, renaming the file
    based on the values from specified columns in the CSV.

    Args:
        input_filepath (Path): A path to a file that needs to be copied.
        student_list (list[dict]): A list of dictionaries containing student data.
        name_fields (list[str]): A list of column names from the CSV to use for
            generating the new filenames. If empty, the first column value will be used.
        output_dir (Path): A directory where the copied files will be saved.
    """
    base = input_filepath.stem
    suffix = input_filepath.suffix

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    for row in student_list:
        filename = [row[field] for field in name_fields]
        filename = "_".join(filename)

        filename = filename + "_" + base + suffix
        filename = filename.replace(" ", "_")  # remove any lingering spaces
        filename = filename.lower()

        # Copy file to new location
        shutil.copyfile(input_filepath, output_dir / filename)


def sort_files(
    sort_dir: Path,
    dest_dir: Path,
    sort_map: dict[str, str],
) -> list[str]:
    """Sorts files into folders.

    Looks for files in `sort_dir` that match KEYS in `sort_map` and copies them
    into subfolders in `dest_dir` based on the corresponding VALUES in `sort_map`.

    Args:
        sort_dir (Path): The directory containing files to be sorted.
        dest_dir (Path): The base directory where sorted files will be placed.
        sort_map (dict[str, str]): A mapping of student identifiers to their corresponding
            destination subfolder names.

    Returns:
        list[str]: A list of filenames that were not found in the source directory.
    """
    missing_files = []

    for filename, subdir in sort_map.items():
        # Create output folder
        output_dir = dest_dir / subdir
        output_dir.mkdir(exist_ok=True, parents=True)

        # Find files that match
        matches = sort_dir.glob(f"*{filename}*")

        if not matches:
            missing_files.append(filename)

        for file in matches:
            shutil.copyfile(file, output_dir / file.name)

    return missing_files


def replace_filename_substr(input_dir: Path, rename_map: dict[str, str]) -> None:
    """Replaces portions of filenames in a directory based on a mapping.

    Useful when filenames contain an id number that needs to be replaced with another.

    Args:
        input_dir (Path): The directory containing files to be renamed.
        rename_map (dict[str, str]): A mapping of old substrings to new substrings for renaming.
    """
    for old_substr, new_substr in rename_map.items():
        for file in input_dir.glob(f"*{old_substr}*"):
            new_name = file.name.replace(old_substr, new_substr)
            new_path = input_dir / new_name
            file.rename(new_path)


def download_file(url: str, output_path: Path) -> None:
    """Downloads a file from a URL to a specified output path.

    Args:
        url (str): The URL of the file to be downloaded.
        output_path (Path): The path where the downloaded file will be saved.
    """
    response = r.get(url, stream=True, timeout=10)
    response.raise_for_status()

    with output_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def unzip_dir(input_file: Path) -> None:
    """Unzips a zip file to a directory.

    Args:
        input_file (Path): The zip file to be extracted.
    """
    output_dir = input_file.parent / (input_file.stem)

    with zipfile.ZipFile(input_file, "r") as zip_ref:
        zip_ref.extractall(output_dir)

    return output_dir


def search_dirs(directories: list[Path], substr: str) -> list[Path]:
    """Searches a list of directories for files matching a given utorid.

    Args:
        directories (list[Path]): A list of directories to search.
        substr (str): The utorid to search for in filenames.

    Returns:
        list[Path]: A list of file paths that match the given utorid.
    """
    matched_files = []

    for directory in directories:
        matches = directory.glob(f"*{substr}*")
        matched_files.extend(matches)

    return matched_files

``
