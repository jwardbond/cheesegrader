"""Quercus Submission and Grading Workflow Utilities.

This module provides a set of tools for controlling uploading grades and files to Quercus.

The core workflow function is `upload()`, which controls the process based on
a specified `UploadMode`.

Functions:
    search_dirs: Searches local directories recursively for files matching a student ID.
    upload_grades: Posts a dictionary of SIS ID-grade pairs to Quercus.
    upload_files: Locates and uploads local files to the corresponding student submissions.
    upload: The main orchestration function combining grade and file uploads.

Classes:
    UploadMode: An Enum defining the types of uploads supported (grades, files, or both).

:copyright: (c) 2025 by Jesse Ward-Bond.
:license: MIT, see LICENSE for more details.
"""

from enum import Enum
from pathlib import Path

# NOTE: Since search_dirs is implemented below, the file_utils import is likely obsolete.
# from file_utils import file_lookup
from src.quercus_assignment import QuercusAssignment


class UploadMode(Enum):
    """Defines the allowed modes for the upload workflow."""

    GRADES = 0
    FILES = 1
    BOTH = 2


def search_dirs(idx: str, dirs: list[Path]) -> list[Path]:
    """Given an ID and a list of directories, returns a list of files that match the ID.

    Searches the provided directories recersively.

    Args:
        idx (str): The identifier to search for in the file name (as a prefix).
        dirs (list[Path]): A list of parent directory paths to search.

    Returns:
        list[Path]: A list of file paths found that match the ID prefix.
    """
    output = []
    for d in dirs:
        matched_files = list(d.rglob(f"{idx}*"))
        output.extend(matched_files)
    return output


def upload_grades(
    assignment: QuercusAssignment,
    grades: dict[str, float],
) -> list[str]:
    """Posts grades to Quercus for the given students.

    Args:
        assignment (QuercusAssignment): The assignment object to post grades to.
        grades (dict[str, float]): A dictionary mapping SIS IDs (str) to grades (float).

    Returns:
        list[str]: A list of error messages for grades that failed to upload.
    """
    error_list = []
    for sis_id, grade in grades.items():
        if grade is None:
            error_list.append(f"{sis_id}: \t Missing grade")
            continue
        try:
            assignment.post_grade(sis_id, grade)
        # TODO: Specify exception, e.g., catch requests.HTTPError or a custom AssignmentPostError
        except Exception:  # noqa: BLE001
            error_list.append(f"{sis_id}: \t Missing student or post failed")

    return error_list


def upload_files(
    assignment: QuercusAssignment,
    lookup_ids: list[str],
    dirs: list[Path],
) -> list[str]:
    """Finds files for the given IDs in the specified directories and uploads them as submissions.

    Args:
        assignment (QuercusAssignment): The assignment object to upload files to.
        lookup_ids (list[str]): A list of SIS IDs to search for in file names.
        dirs (list[Path]): A list of directories to recursively search for files.

    Returns:
        list[str]: A list of error messages for files that were not found or failed to upload.
    """
    error_list = []
    for lid in lookup_ids:
        files = search_dirs(lid, dirs)

        if not files:
            error_list.append(f"{lid}: \t No files found")
        if len(files) < len(dirs):
            error_list.append(f"{lid}: \t Fewer files found than directories searched. Likely missing files.")
        else:
            for f in files:
                try:
                    assignment.upload_file(lid, f)
                # TODO: Specify exception, e.g., catch requests.HTTPError or a custom FileUploadError
                except Exception:  # noqa: BLE001
                    error_list.append(f"{lid}: \t Upload failed for {f.name}")
    return error_list


def upload(
    assignment: QuercusAssignment,
    grades: dict[str, float],  # Fixed type hint
    lookup_ids: list[str],
    dirs: list[Path],
    mode: UploadMode,
) -> list[str]:
    """Controls the upload workflow for grades and/or files.

    Args:
        assignment (QuercusAssignment): The assignment object to use for API calls.
        grades (dict[str, float]): A dictionary mapping SIS IDs to grades.
        lookup_ids (list[str]): A list of SIS IDs to search for in file names.
        dirs (list[Path]): A list of directories to recursively search for files to upload.
        mode (UploadMode): Specifies whether to upload grades, files, or both.

    Returns:
        list[str]: A consolidated list of error messages from the upload process.
    """
    error_list = []

    if mode in (UploadMode.GRADES, UploadMode.BOTH):
        error_list.extend(upload_grades(assignment, grades))

    if mode in (UploadMode.FILES, UploadMode.BOTH):
        error_list.extend(upload_files(assignment, lookup_ids, dirs))

    return error_list
