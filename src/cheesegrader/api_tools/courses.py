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
