import pathlib

import pytest

from src.quercus_assignment import QuercusAssignment


@pytest.fixture
def quercus_assignment(mocker):
    # Patch r.get used in __init__ to avoid real network calls
    mock_get = mocker.patch("src.quercus_assignment.r.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "name": "Test Assignment",
        "group_category_id": None,
    }

    course_id = "123456"
    assignment_id = "654321"
    auth_key = "123authtokenabc"

    return QuercusAssignment(
        course_id=course_id,
        assignment_id=assignment_id,
        auth_key=auth_key,
    )


class FakePostResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json


def test_post_grade(quercus_assignment, mocker):
    # --- Setup ---

    # Patch PUT
    mock_put = mocker.patch("src.quercus_assignment.r.put")
    mock_put.return_value.status_code = 200

    # Get test data
    student_id = "sta1"
    grade = 95.0

    # Call the method
    quercus_assignment.post_grade(user_id=student_id, grade=grade)

    # --- Assertions ---

    # Check that r.post was called with correct parameters
    mock_put.assert_called_once_with(
        f"https://q.utoronto.ca/api/v1/courses/{quercus_assignment.course_id}/assignments/{quercus_assignment.assignment_id}/submissions/sis_user_id:{student_id}",
        data={"submission[posted_grade]": f"{grade:.1f}"},
        headers=quercus_assignment.auth_key,
        timeout=10,
    )


def test_upload_file(quercus_assignment, mocker):
    # --- Setup ---

    # Patch first two POST requests
    mock_post = mocker.patch("src.quercus_assignment.r.post")
    mock_post.side_effect = [
        FakePostResponse(
            {
                "upload_url": "http://example.com/upload",
                "upload_params": {"testkey": "testvalue"},
            },
        ),
        FakePostResponse(
            {
                "id": "fid123",
            },
        ),
    ]

    # Patch file open to avoid actual file I/O
    mock_open = mocker.patch(
        "pathlib.Path.open",
        mocker.mock_open(read_data="filedata"),
    )

    # Patch the final PUT request
    mock_put = mocker.patch("src.quercus_assignment.r.put")
    mock_put.return_value.status_code = 200

    # Get filepaths
    student_id = "sta1"
    filepath = pathlib.Path("./tests/test_data/test_rubrics/1/sta1_rubric.pdf")

    # Call the method
    quercus_assignment.upload_file(user_id=student_id, filepath=filepath)

    # --- Assertions ---

    # First POST must be called correctly
    mock_post.assert_any_call(
        f"https://q.utoronto.ca/api/v1/courses/{quercus_assignment.course_id}/assignments/{quercus_assignment.assignment_id}/submissions/sis_user_id:{student_id}/comments/files",
        data={
            "name": filepath.name,
            "size": filepath.stat().st_size,
        },
        headers=quercus_assignment.auth_key,
        timeout=10,
    )

    # Secdond POST must be called correctly with correct upload params
    mock_post.assert_any_call(
        "http://example.com/upload",
        files={"upload_file": mock_open.return_value},
        data={"testkey": "testvalue"},
        timeout=10,
    )

    # PUT: link file to comment
    mock_put.assert_called_once_with(
        f"https://q.utoronto.ca/api/v1/courses/{quercus_assignment.course_id}/assignments/{quercus_assignment.assignment_id}/submissions/sis_user_id:{student_id}",
        data={
            "comment[file_ids]": ["fid123"],
            "comment[group_comment]": "true",
        },
        headers=quercus_assignment.auth_key,
        timeout=10,
    )
