import os
import pathlib
from glob import glob

import requests as r


class QuercusAssignment(object):
    """A class to interact with the Quercus API for uploading and managing course assignments.

    This class provides methods for accessing course details, student lists, and student submissions for courses at UofT, and provides methods for uploading grades/rubrics.

    Most of this code has been adapted from # TODO I forgot where I got it lol

    Attributes:
        course_id (str): The course number on Quercus
        assignment_id (str, optional): The assignment number on Quercus (if provided)
        auth_key (dict): The auth token for canvas API. See Readme for more details.
        endpoints (dict): A collection of API endpoint URLs related to the course, assignment, submissions, groups, and students.
        course (dict): The course information fetched from the API.
        assignment (dict): The assignment information fetched from the API.
        group_ids (list): A list of group IDs associated with the course.
        students (dict): A dictionary of records for students enrolled in the course

    Methods:
        _get_course(): Fetches course information from the Quercus API.
        _get_assignment(): Fetches assignment information from the Quercus API.
        _get_groups(): Fetches group IDs associated with the course.
        _get_student_list(): Fetches the list of students enrolled in the course.

    """

    def __init__(self, course_id, assignment_id, auth_key):
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

        self.assignment = self._get_assignment()
        self.assignment_id = assignment_id
        self.group_ids = self._get_groups()

    def _get_assignment(self):
        url = self.endpoints["assignment"]
        response = r.get(url, headers=self.auth_key)

        return response.json()

    def _get_groups(self):
        if self.is_group():
            url = self.endpoints["groups"] + str(self.assignment["group_category_id"]) + self.endpoints["groups_suffix"]

            data = {"include": ["users"]}
            params = {"per_page": 200}

            response = r.get(url, params=params, data=data, headers=self.auth_key)

            group_data = response.json()

            group_ids = {}

            print(f"Data length: {len(group_data)}")

            if len(group_data) > 0:
                for group in group_data:
                    group_ids[group["name"]] = group["id"]

            links = response.headers["Link"].split(",")

            while len(links) > 1 and "next" in links[1]:
                next_url = links[1].split("<")[1].split(">")[0].strip()
                print(next_url)
                response = r.get(next_url, headers=self.auth_key)

                print(response.headers["Link"])

                group_data = response.json()

                print(response.status_code)
                print(response.content)
                print(group_data)

                print(f"Data length: {len(group_data)}")

                if len(group_data) > 0:
                    for group in group_data:
                        group_ids[group["name"]] = group["id"]

                links = response.headers["Link"].split(",")

            return group_ids

        else:
            return None

    def get_assignment_title(self):
        return self.assignment["name"]

    def is_group(self):
        return self.assignment["group_category_id"] is not None

    def group_data_parser(self, group_info):
        """Given group info (id, grade), returns individual student info (id, group grade).

        Args:
            group_info: todo

        Returns:
            list: a list of dicts containing student grading information
        """

        url = self.endpoints["group_users"] + str(self.group_ids[group_info["id"]]) + self.endpoints["group_users_suffix"]

        params = {"per_page": 20}

        response = r.get(url, params=params, headers=self.auth_key)

        parsed_data = []

        for user in response.json():
            parsed_data.append(
                {
                    "id": user[
                        "sis_user_id"
                    ],  # TODO verify that this is actually the SIS user_id, since all other functions use UTORID and idk if they are interchangeable
                    "grade": group_info["grade"],
                    "group_id": group_info["id"],
                }
            )

        return parsed_data

    def post_grade(self, user_id, grade):
        """Posts the grade for a given user.

        Args:
            user_id (int): Quercus sis_id for the user
            grade (float): Grade for the user
        """
        # update the grade
        url = self.endpoints["submission"] + f"{user_id}"
        grade_info = {"submission[posted_grade]": f"{grade:.1f}"}
        response = r.put(url, data=grade_info, headers=self.auth_key)

    def upload_file(self, user_id: int, filepath: pathlib.Path):
        """Uploads a single file for a given user.

        Args:
            user_id (int): Quercus sis_id for the user
            filepaths (list): A list of filepaths to search for relevant files
        """
        # based on this post: https://community.canvaslms.com/t5/Canvas-Developers-Group/API-Assignment-Comments-File-Upload/td-p/176229
        url = self.endpoints["submission"] + f"{user_id}" + self.endpoints["submission_comments_suffix"]

        # Step 1: Get upload URL
        name = filepath.name
        size = filepath.stat().st_size
        file_info = {
            "name": name,
            "size": size,
            "content_type": "application/docx",
        }
        response = r.post(url, data=file_info, headers=self.auth_key)

        # Step 2: Upload file
        upload_url = response.json()["upload_url"]
        upload_params = response.json()["upload_params"]
        file_data = {"upload_file": filepath.open("rb")}
        response = r.post(upload_url, files=file_data, data=upload_params)

        # Step 3: Link uploaded file id with comment
        file_id = response.json()["id"]

        comment_url = f"https://q.utoronto.ca/api/v1/courses/{self.course_id}/assignments/{self.assignment_id}/submissions/sis_user_id:{user_id}"

        comment_info = {
            "comment[file_ids]": [file_id],
            "comment[group_comment]": "true",
        }

        response = r.put(comment_url, data=comment_info, headers=self.auth_key)
