import pathlib

import pandas as pd
import requests as r
from click import prompt

from .quercus_assignment import QuercusAssignment


class QuercusCourse:
    """A course object for interacting with a Quercus course through Canvas APIs.

    This class provides methods for accessing course details, student lists, and student submissions.

    Attributes:
        course_id (str, int): The course number on Quercus
        auth_key (dict): The Authorization header dictionary for Canvas API requests. i.e. {'Authorization': 'Bearer <token>'}
        endpoints (dict): A collection of API endpoint URLs related to the course.
        course (dict): The course information fetched from the API.
        students (dict): A dictionary of records for students enrolled in the course
        assignment (QuercusAssignment, optional): An assignment object used for uploading and downloading grades

    Methods:
        _get_course(): Fetches course information from the Quercus API.
        _get_assignment(): Fetches assignment information from the Quercus API.
        generate_student_dataframe():

    """

    def __init__(self, course_id: str | int, token: str) -> None:
        self.auth_key = {"Authorization": f"Bearer {token}"}
        self.course_id = course_id

        self.endpoints = {
            "course": f"https://q.utoronto.ca/api/v1/courses/{course_id}/",
            "students": f"https://q.utoronto.ca/api/v1/courses/{course_id}/students",
        }

        self.course_info = self._get_course()
        self.students = self._get_student_list()

    def _get_course(self):
        # based on this post: https://canvas.instructure.com/doc/api/assignments.html#method.assignments_api.show
        url = self.endpoints["course"]
        response = r.get(url, headers=self.auth_key)

        return response.json()

    def _get_student_list(self):
        url = self.endpoints["students"]
        response = r.get(url, headers=self.auth_key)

        return response.json()

    def generate_student_dataframe(self) -> pd.DataFrame:
        """Generates a dataframe of student information for the course.

        Returns:
            pd.DataFrame: A dataframe with the following columns
                - sis_user_id: The student's unique identifier on Quercus
                - id: The student's UTORid.
                - integration_id: The ID used for integrations (usually the same as UTORid)
                - name: The full name of the student (First Middle Last)
                - sortable_name: A format of the name suitable for sorting (Last, First Middle)
                - fname: The first name of the student
                - lname: The last name of the student
        """
        raw_df = pd.DataFrame.from_records(self.students)
        cleaned_df = raw_df.drop_duplicates()
        cleaned_df = cleaned_df.loc[
            :,
            [
                "sis_user_id",
                "id",
                "integration_id",
                "name",
                "sortable_name",
            ],
        ]

        cleaned_df["fname"] = cleaned_df["sortable_name"].apply(lambda s: s.split(", ")[1])
        cleaned_df["lname"] = cleaned_df["sortable_name"].apply(lambda s: s.split(", ")[0])

        print(f"Generated student dataframe and dropped {len(raw_df) - len(cleaned_df)} duplicate records")

        return cleaned_df

    def upload(
        self,
        assignment_id: int,
        grade_filepath: pathlib.Path,
        mode: int = 0,
        upload_filepaths: list[pathlib.Path] | None = None,
    ) -> None:
        """# TODO"""
        # TODO add NAN test for uploads incase there are a lot of extra rows in the csv
        if upload_filepaths is None:
            upload_filepaths = []

        assignment = QuercusAssignment(self.course_id, assignment_id, self.token)

        print(
            f"This will add grades and upload grades for {assignment.get_assignment_title()} in {self.get_course_title()}\n",
        )

        if (
            prompt(
                "Are you sure you want to proceed? (Y/N)",
                default="N",
                show_default=True,
            )
            == "Y"
        ):
            # Get grading file
            grades_df = pd.read_csv(grade_filepath)

            missing_files = []
            for row in grades_df.iterrows():
                print(f"{row[1]['id']} \t {row[1]['grade']}")
                data = []

                if assignment.is_group():
                    data = assignment.group_data_parser(row[1])
                else:
                    data.append(row[1])

                for student in data:
                    idx = student["id"]
                    grade = student["grade"]

                    # Upload files
                    if mode in (0, 2):  # Upload files
                        # Find files for given idx
                        files = file_lookup(idx, upload_filepaths)

                        if len(files) == 0:  # file missing
                            missing_files.append(idx)
                        else:  # upload files
                            for f in files:
                                assignment.upload_file(
                                    idx, f, student["group_id"]
                                ) if assignment.is_group() else assignment.upload_file(idx, f)

                    # Upload grades
                    if mode in (0, 1):  # Upload grades
                        assignment.post_grade(idx, grade)

        for missing in missing_files:
            print(missing)

    # Get the course title based on the course id
    def get_course_title(self) -> str:
        return self.course_info["name"]


def file_lookup(idx: str, parent_paths: list[pathlib.Path]) -> list[pathlib.Path]:
    """Given an id and a list of parent paths, returns a list of files that match the id.

    Searches parent paths recursively.

    Args:
        idx (str): The id to search for in the file name
        parent_paths (list[pathlib.Path]): A list of parent paths to search for the id

    """
    output = []
    for path in parent_paths:
        try:
            matched_files = list(path.rglob(f"{idx}*"))
            output = output + matched_files
        except IndexError:
            continue
    return output
