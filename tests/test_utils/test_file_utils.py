import zipfile
from pathlib import Path

from cheesegrader.utils import replace_filename_substr, unzip_dir


def test_unzip_dir(tmp_path):
    """Tests that unzip_dir correctly extracts files from a zip archive into the specified directory."""
    # Create a sample zip file
    tmp_dir = Path("../test_data/") / tmp_path
    zip_file_path = tmp_dir / "test_archive.zip"

    # Create some files to zip
    files = {
        "file1.txt": "This is the content of file 1.",
        "file2.txt": "This is the content of file 2.",
        "subdir/file3.txt": "This is the content of file 3 in a subdirectory.",
    }
    for file_path, content in files.items():
        full_path = tmp_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with full_path.open("w") as f:
            f.write(content)

    # Create the zip file
    with zipfile.ZipFile(zip_file_path, "w") as zipf:
        for file_path in files:
            zipf.write(tmp_dir / file_path, arcname=file_path)

    # Extract
    save_dir = unzip_dir(zip_file_path)

    # Output dir should be the zip file name without .zip
    assert save_dir == zip_file_path.parent / zip_file_path.stem

    # Output dir should exist
    assert save_dir.exists()

    for file_path, file_contents in files.items():
        # Files should exist
        assert (save_dir / file_path).exists()

        # Files should have correct content
        with (save_dir / file_path).open("r") as f:
            assert f.read() == file_contents


def test_replace_filename_substr(tmp_path):
    """Tests that replace_filename_substr correctly renames files in a directory based on a mapping."""
    # Create sample files
    tmp_dir = Path("../test_data/") / tmp_path
    filenames = ["student123_assignment1.txt", "gabagool_student456_assignment1.txt", "student123_assignment2.txt"]
    for filename in filenames:
        with (tmp_dir / filename).open("w") as f:
            f.write("Sample content")

    # Define rename map
    rename_map = {
        "student123": "utorid_abc",
        "student456": "utorid_def",
    }

    # Perform renaming
    replace_filename_substr(tmp_dir, rename_map)

    # Check that files have been renamed correctly
    expected_filenames = [
        "utorid_abc_assignment1.txt",
        "gabagool_utorid_def_assignment1.txt",
        "utorid_abc_assignment2.txt",
    ]
    for expected_filename in expected_filenames:
        assert (tmp_dir / expected_filename).exists()
