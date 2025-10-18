from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from cheesegrader.cli.uploading import prompt_get_csv


# Helper fixture to mock typer.secho and prevent output during tests
@pytest.fixture(autouse=True)
def mock_secho(mocker: MockerFixture):
    """Mocks typer.secho to prevent printing to the terminal during tests."""
    mocker.patch("typer.secho")


def test_prompt_get_csv(mocker: MockerFixture):
    """Get a csv with the correct column names already existing"""

    csv_path = Path(__file__).parents[1] / "test_data" / "grades.csv"

    prompt_mock = mocker.patch("typer.prompt")
    prompt_mock.side_effect = [
        csv_path.resolve(),
    ]

    expected_data = [
        {"id": "1001", "grade": "95"},
        {"id": "1002", "grade": "88"},
        {"id": "1003", "grade": "72"},
    ]
    expected_header_map = {"id": "id", "grade": "grade"}

    data, path, header_map = prompt_get_csv(required_headers={"id", "grade"})

    assert path.resolve() == csv_path.resolve()
    assert data == expected_data
    assert header_map == expected_header_map
