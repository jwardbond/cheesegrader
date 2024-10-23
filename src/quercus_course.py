import pathlib
from glob import glob

from click import prompt
import requests as r
import pandas as pd

from .quercus_assignment import QuercusAssignment


class QuercusCourse(object):
    """A course object for interacting with Quercus through Canvas APIs

    This class provides methods for accessing course details, student lists, and student submissions for courses at UofT, and provides methods for uploading grades/rubrics.

    Most of this code has been adapted from # TODO I forgot where I got it lol

    Attributes:
        auth_key (str): The authentication token for Canvas APIs. See ReadMe for more details.
        course_id (str): The course number on Quercus
        endpoints (dict): A collection of API endpoint URLs related to the course.
        course (dict): The course information fetched from the API.
        students (dict): A dictionary of records for students enrolled in the course
        assignment (QuercusAssignment, optional): An assignment object used for uploading and downloading grades

    Methods:
        _get_course(): Fetches course information from the Quercus API.
        _get_assignment(): Fetches assignment information from the Quercus API.
        generate_student_dataframe():

    """

    def __init__(self, course_id, auth_key) -> None:
        self.token = auth_key
        self.auth_key = {"Authorization": f"Bearer {auth_key}"}
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

    def generate_student_dataframe(self):
        """Generates a dataframe of student information for the course

        Returns:
            pd.DataFrame: A dataframe with the following columns
                - sis_user_id: The student's unique identifier on Quercus
                - id: The student's UTORid.
                - integration_id: The ID used for integrations (usually the same as UTORid)
                - name: The full name of the student (First Middle Last)
                - sortable_name: A format of the name suitable for sorting (Last, First Middle)
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

        cleaned_df["fname"] = cleaned_df["sortable_name"].apply(
            lambda s: s.split(", ")[1]
        )
        cleaned_df["lname"] = cleaned_df["sortable_name"].apply(
            lambda s: s.split(", ")[0]
        )

        print(
            f"Generated student dataframe and dropped {len(raw_df) - len(cleaned_df)} duplicate records"
        )

        return cleaned_df

    # TODO handle when assignment is not found in course
    def upload_grades(
        self, assignment_id: int, grade_file_path: pathlib.Path, file_paths=[]
    ):
        """# TODO"""
        assignment = QuercusAssignment(self.course_id, assignment_id, self.token)

        print(
            f"This will add grades and upload grades for {assignment.get_assignment_title()} in {self.get_course_title()}\n"
        )

        if "Y" == prompt(
            "Are you sure you want to proceed? (Y/N)", default="N", show_default=True
        ):
            # Get grading file
            grades_df = pd.read_csv(grade_file_path)

            missing_files = []
            for row in grades_df.iterrows():
                print(f'{row[1]["id"]} \t {row[1]["grade"]}')
                data = []

                if assignment.is_group():
                    data = assignment.group_data_parser(row[1])
                else:
                    data.append(row[1])

                for student in data:
                    id = student["id"]
                    grade = student["grade"]

                    # post grade
                    assignment.post_grade(id, grade)

                    # upload files
                    if file_paths:
                        status, name, folder = (
                            assignment.upload(id, file_paths, student["group_id"])
                            if assignment.is_group()
                            else assignment.upload(id, file_paths)
                        )
                        if status == 0:
                            missing_files.append([name, folder])
        print(missing_files)

    # Get the course title based on the course id
    def get_course_title(self):
        return self.course_info["name"]
