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

        self.course = self._get_course()
        self.students = self._get_student_list()

    @property
    def course_name(self) -> str:
        """Returns the name of the course."""
        return self.course["name"]

    def generate_student_dataframe(self) -> pd.DataFrame:
        """Generates a dataframe of student information for the course.

        Returns:
            pd.DataFrame: A dataframe with the following columns
                - sis_user_id: The student's unique identifier on Quercus
                - id: The student's UTORid.
                - integration_id: Usually the student number
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

    def upload_assignment_grades(self, assignment_id: int, grades: dict) -> None:
        """Uploads grades for a specific assignment.

        Args:
            assignment_id (int): The assignment ID number on Quercus.
            grades (dict): A dictionary mapping canvas SIS ids respective grades. {sis_id: grade}
        """
        assignment = QuercusAssignment(self.course_id, assignment_id, self.token)

        for student, grade in grades.items():
            assignment.post_grade(student, grade)
