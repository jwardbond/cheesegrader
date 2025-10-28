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
            "submissions": (
                f"https://q.utoronto.ca/api/v1/courses/{course_id}/assignments/{assignment_id}/"
                "submissions?per_page=100&include[]=submission_comments"
            ),
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
    def name(self) -> str:
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

    @property
    def submissions(self) -> list:
        """Returns the list of submissions for the assignment."""
        if not hasattr(self, "_submissions"):
            url = self.endpoints["submissions"]
            submissions = []
            while url:
                response = r.get(url, headers=self.auth_key, timeout=10)
                submissions.extend(response.json())
                url = response.links.get("next", {}).get("url")
            self._submissions = submissions
        return self._submissions

    def download_submissions(self, destination: Path) -> None:
        """Downloads the submissions zip file for the assignment.

        Args:
            destination (Path): The path where the zip file will be saved.
        """
        url = self.endpoints["submissions"]
        headers = self.auth_key
        destination.mkdir(parents=True, exist_ok=True)

        # Ensure filenames contain utorid
        id_utorid_map = self.course.get_id_utorid_map()

        # Loop through api pages and construct submissions list
        job_list = []
        for submission in self.submissions:
            for attachment in submission.get("attachments", []):
                attachment_url = attachment["url"]
                user_id = str(submission["user_id"])
                utorid = str(id_utorid_map.get(user_id, user_id))

                filename = utorid + "_" + attachment["display_name"]

                # Because students insert crazy symbols in filenames
                filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", filename).strip().rstrip(". ")
                filepath = destination / filename

                job_list.append({"path": filepath, "url": attachment_url})

        # Download the files to the output directory
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(download_file, job["url"], job["path"]) for job in job_list]
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
            self.endpoints["group_users"]
            + str(self.group_ids[group_info["id"]])
            + self.endpoints["group_users_suffix"]
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
        url = (
            self.endpoints["submission"]
            + f"{sis_id}"
            + self.endpoints["submission_comments_suffix"]
        )

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
                error_list.append(f"{utorid}:      Missing grade")
                continue

            try:
                self.post_grade(utorid, grade)
            except Exception:  # noqa: BLE001
                error_list.append(f"{utorid}:      Missing student or post failed")

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
        for student_id, files in tqdm(student_files.items()):
            if not files:
                error_list.append(f"{student_id}: No files found for upload")
                continue

            for file in files:
                try:
                    self.upload_file(student_id, file)
                except Exception:  # noqa: BLE001
                    error_list.append(f"{student_id}: Upload failed for {file.name}")

        return error_list

    def get_comment_authors(self, instructor_only: bool = True) -> dict[int, str]:
        """Returns a dictionary of author IDs and names for submission comments.

        Args:
            instructor_only (bool): If True, only include comments made by instructors and TAs.

        Returns:
            dict[int, str]: A dictionary mapping author IDs to their names.
        """
        authors = {}
        allowed_ids = set()
        if instructor_only:
            allowed_ids = {instr["id"] for instr in self.course.instructors}

        for submission in self.submissions:
            for comment in submission.get("submission_comments", []):
                author_id = comment["author_id"]
                author_name = comment["author_name"]

                if (len(allowed_ids) == 0) or (author_id in allowed_ids):
                    authors[author_id] = author_name

        return authors

    def delete_comments(self, authors: dict[int, str]) -> list[dict]:
        """Deletes all submission comments made by the specified authors.

        Done in two steps to allow possibility of multi-threading later.

        Args:
            authors (dict[int, str]): A dictionary mapping author IDs to their names.

        Returns:
            list[dict]: A dictionary of errors encountered during deletion.
        """
        id_utorid_map = self.course.get_id_utorid_map()
        errors = {}

        # Build list of comments to delete
        jobs = []
        for submission in self.submissions:
            utorid = id_utorid_map[submission["user_id"]]
            for comment in submission.get("submission_comments", []):
                if comment["author_id"] in authors:
                    jobs.append((utorid, comment["author_id"], comment["id"]))

        # Delete comments
        for utorid, author_id, comment_id in tqdm(jobs):
            url = f"{self.endpoints['submission']}{utorid}/comments/{comment_id}"
            response = r.delete(url, headers=self.auth_key, timeout=10)
            if not response.ok:
                errors[utorid] = f"Failed to delete comment by {authors[author_id]}"

        return errors

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
