"""Quercus Assignment API Client.

This module provides the QuercusAssignment class for interacting with the
Canvas/Quercus LMS API, specifically for managing assignments, submissions,
grades, and file uploads.

Classes:
    QuercusAssignment: The primary client class for assignment management.

TODO:
    * Implement batch submission/grade updates.
    * Implement deletion of submission comments.

:copyright: (c) 2025 by Jesse Ward-Bond.
:license: MIT, see LICENSE for more details.
"""

import pathlib

import requests as r


class QuercusAssignment:
    """A class to interact with the Quercus API for uploading and managing course assignments.

    This class provides methods for accessing assignment details, and uploading grades/rubrics.

    Attributes:
        course_id (str, int): The course number on Quercus
        auth_key (dict): The Authorization header dictionary for Canvas API requests. i.e. {'Authorization': 'Bearer <token>'}
        endpoints (dict): A collection of API endpoint URLs related to the assignment.
        assignment (dict): The assignment information fetched from the API.
        group_ids (list): A list of group IDs associated with the course.
    """

    def __init__(self, course_id: int, assignment_id: int, auth_key: str) -> None:
        """Initializes the QuercusAssignment object and fetches initial data.

        Args:
            course_id (int): The course ID number on Quercus.
            assignment_id (int): The assignment ID number on Quercus.
            auth_key (str): The raw authentication token (string). Details about this are in the README.
        """
        self.course_id = course_id
        self.assignment_id = assignment_id
        self.auth_key = {"Authorization": f"Bearer {auth_key}"}
        self.endpoints = {
            "course": f"https://q.utoronto.ca/api/v1/courses/{course_id}/",
            "assignment": f"https://q.utoronto.ca/api/v1/courses/{course_id}/assignments/{assignment_id}",
            "submission": f"https://q.utoronto.ca/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/sis_user_id:",
            "submission_comments_suffix": "/comments/files",
            "groups": "https://q.utoronto.ca/api/v1/group_categories/",
            "groups_suffix": "/groups",
            "group_users": "https://q.utoronto.ca/api/v1/groups/",
            "group_users_suffix": "/users",
        }

        # Fetch assignment info
        self.assignment = self._get_assignment()
        self.group_ids = self._get_groups()

    @property
    def assignment_name(self) -> str:
        """Returns the name of the assignment."""
        return self.assignment["name"]

    @property
    def is_group(self) -> bool:
        """Returns whether the assignment is a group assignment."""
        return self.assignment["group_category_id"] is not None

    def _get_assignment(self):
        url = self.endpoints["assignment"]
        response = r.get(url, headers=self.auth_key, timeout=10)

        return response.json()

    def _get_groups(self) -> dict | None:
        if self.is_group:
            url = self.endpoints["groups"] + str(self.assignment["group_category_id"]) + self.endpoints["groups_suffix"]

            data = {"include": ["users"]}
            params = {"per_page": 200}

            response = r.get(url, params=params, data=data, headers=self.auth_key, timeout=10)

            group_data = response.json()

            group_ids = {}

            if len(group_data) > 0:
                for group in group_data:
                    group_ids[group["name"]] = group["id"]

            links = response.headers["Link"].split(",")

            while len(links) > 1 and "next" in links[1]:
                next_url = links[1].split("<")[1].split(">")[0].strip()
                response = r.get(next_url, headers=self.auth_key, timeout=10)

                group_data = response.json()

                if len(group_data) > 0:
                    for group in group_data:
                        group_ids[group["name"]] = group["id"]

                links = response.headers["Link"].split(",")

            return group_ids

        return None

    def group_data_parser(self, group_info: dict) -> list:
        """Given group info (ID, grade), returns individual student info (ID, group grade).

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

    def post_grade(self, user_id: str, grade: float) -> bool:
        """Posts the grade for a given user.

        Args:
            user_id: The Quercus sis_id for the user.
            grade: The grade (float) to be posted for the user.

        Returns:
            bool: True if the request was successful (HTTP status 2xx), False otherwise.
        """
        url = self.endpoints["submission"] + f"{user_id}"
        grade_info = {"submission[posted_grade]": f"{grade:.1f}"}
        response = r.put(url, data=grade_info, headers=self.auth_key, timeout=10)

        return response.ok

    def upload_file(self, user_id: int, filepath: pathlib.Path) -> None:
        """Uploads a single file for a given user.

        Api docs for uploading a file: https://developerdocs.instructure.com/services/canvas/basics/file.file_uploads
        Api docs for attaching uploaded file to comment: https://developerdocs.instructure.com/services/canvas/resources/submissions#method.submissions_api.create_file

        Args:
            user_id (int): Quercus sis_id for the user
            filepath (pathlib.Path): Path to the file to be uploaded
        Returns:
            bool: True if the final linkig was successful (HTTP status 2xx), False otherwise.
        """
        url = self.endpoints["submission"] + f"{user_id}" + self.endpoints["submission_comments_suffix"]

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
        submission_url = self.endpoints["submission"] + f"{user_id}"
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
