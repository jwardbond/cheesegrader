import pathlib

from cheesegrader.utils.bulk_uploads import search_dirs


def test_search_dirs_finds_all_files():
    """Tests that search_dirs correctly finds all files matching a prefix ('sta1') across multiple specified directories, including subdirectories (due to rglob)."""
    lookup_folders_str = ["./tests/test_data/test_rubrics/1", "./tests/test_data/test_rubrics/two"]
    lookup_folders = [pathlib.Path(f) for f in lookup_folders_str]

    result = search_dirs("sta1", lookup_folders)

    expected_files_str = [
        "./tests/test_data/test_rubrics/1/sta1_rubric.pdf",
        "./tests/test_data/test_rubrics/1/sta1_other_file1.pdf",
        "./tests/test_data/test_rubrics/two/sta1_other_file2.pdf",
        # If there were files in subdirectories, they would go here too
    ]

    # Normalize paths
    expected_files = {pathlib.Path(f).resolve() for f in expected_files_str}
    result_resolved = {p.resolve() for p in result}

    assert result_resolved == expected_files
