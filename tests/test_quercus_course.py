import pathlib
import unittest
from unittest.mock import MagicMock, call, patch

import pandas as pd

from src.quercus_course import QuercusCourse, file_lookup


class TestQuercusCourse(unittest.TestCase):
    @patch("src.quercus_course.r.get")
    def setUp(self, mock_get):
        # Mock the response for the API call made during the initialization of QuercusCourse
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"name": "Test Course"}

        self.course_id = "123456"
        self.auth_key = "123authtokenabc"

        self.obj = QuercusCourse(course_id=self.course_id, auth_key=self.auth_key)

    @patch("src.quercus_course.prompt")
    @patch("src.quercus_course.QuercusAssignment")
    def test_upload_not_group(self, MockQuercusAssignment, mock_prompt):
        mock_assignment = MockQuercusAssignment.return_value
        mock_assignment.get_assignment_title.return_value = "Test Assignment"
        mock_assignment.is_group.return_value = False

        mock_assignment.upload.return_value = None
        mock_assignment.post_grade.return_value = None

        mock_prompt.return_value = "Y"

        input_csv = pathlib.Path("./tests/test_data/grades.csv")
        input_filepaths = [pathlib.Path("./tests/test_data/test_rubrics")]

        self.obj.upload(assignment_id=654321, grade_filepath=input_csv, mode=0, upload_filepaths=input_filepaths)

        # Construct the expected calls
        df = pd.read_csv(input_csv)
        students = df.id.to_list()
        grades = df.grade.to_list()

        files = [(s, file_lookup(s, input_filepaths)) for s in students]
        files = [(s, f) for s, file_list in files for f in file_list]

        post_grade_calls = [call(s, g) for s, g in zip(students, grades)]
        upload_calls = [call(s, f) for s, f in files]

        # Assert the right calls are made
        mock_assignment.post_grade.assert_has_calls(post_grade_calls)
        mock_assignment.upload.assert_has_calls(upload_calls)

    def test_file_lookup(self):
        lookup_folders = ["./tests/test_data/test_rubrics/1", "./tests/test_data/test_rubrics/two"]
        lookup_folders = [pathlib.Path(f) for f in lookup_folders]

        result = file_lookup("sta1", lookup_folders)
        files = [
            "./tests/test_data/test_rubrics/1/sta1_rubric.pdf",
            "./tests/test_data/test_rubrics/1/sta1_other_file1.pdf",
            "./tests/test_data/test_rubrics/two/sta1_other_file2.pdf",
        ]
        files = [pathlib.Path(f).resolve() for f in files]

        result = [p.resolve() for p in result]

        self.assertEqual(len(result), 3)
        self.assertTrue(all(f in files for f in result))
