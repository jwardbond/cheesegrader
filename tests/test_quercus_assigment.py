import pathlib
import unittest
from unittest.mock import MagicMock, patch

from src.quercus_assignment import QuercusAssignment


class TestQuercusAssignment(unittest.TestCase):
    @patch("src.quercus_assignment.r.get")
    def setUp(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"name": "Test Assignment", "group_category_id": None}  # Response for _get_assignment

        self.course_id = "123456"
        self.assigment_id = "654321"
        self.auth_key = "123authtokenabc"

        self.obj = QuercusAssignment(course_id=self.course_id, assignment_id=self.assigment_id, auth_key=self.auth_key)

    @patch("src.quercus_assignment.r.post")
    @patch("src.quercus_assignment.r.put")
    def test_upload_file_indiv(self, mock_put, mock_post):
        mock_post.side_effect = [
            MagicMock(status_code=200, json=lambda: {"upload_url": "http://example.com/upload", "upload_params": {"testkey": "testvalue"}}),
            MagicMock(status_code=200, json=lambda: {"id": "fid123"}),
        ]

        # Create a mock response for the PUT request
        mock_put.return_value.status_code = 200

        # Create an instance of QuercusAssignment
        obj = self.obj

        # Get filepaths
        student_id = "sta1"
        filepath = pathlib.Path("./tests/test_data/test_rubrics/1/sta1_rubric.pdf")

        # Call the method
        result = obj.upload_file(user_id=student_id, filepath=filepath)

        # Check that the call to get an upload URL was made
        mock_post.assert_any_call(
            f"https://q.utoronto.ca/api/v1/courses/{self.course_id}/assignments/{self.assigment_id}/submissions/sis_user_id:{student_id}/comments/files",
            data={"name": filepath.name, "size": filepath.stat().st_size, "content_type": "application/docx"},
            headers={"Authorization": f"Bearer {self.auth_key}"},
        )

        # Check that the call to upload the file was made
        mock_post.assert_any_call("http://example.com/upload", files={"upload_file": unittest.mock.ANY}, data={"testkey": "testvalue"})

        # Check that the comment linking call was made
        mock_put.assert_called_once_with(
            f"https://q.utoronto.ca/api/v1/courses/{self.course_id}/assignments/{self.assigment_id}/submissions/sis_user_id:{student_id}",
            data={"comment[file_ids]": ["fid123"], "comment[group_comment]": "true"},
            headers={"Authorization": f"Bearer {self.auth_key}"},
        )
