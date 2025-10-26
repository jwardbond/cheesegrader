import shutil
from pathlib import Path


def copy_rename(
    input_filepath: Path,
    student_list: list[dict],
    name_fields: list[str],
    output_dir: Path,
) -> None:
    """Copies a file and renames it according to user-specified columns in a class .csv file.

    This function reads a CSV file containing student information, and for each student,
    it copies a specified input file to a designated output directory, renaming the file
    based on the values from specified columns in the CSV.

    Args:
        input_filepath (Path): A path to a file that needs to be copied.
        student_list (list[dict]): A list of dictionaries containing student data.
        name_fields (list[str]): A list of column names from the CSV to use for
            generating the new filenames. If empty, the first column value will be used.
        output_dir (Path): A directory where the copied files will be saved.
    """
    base = input_filepath.stem
    suffix = input_filepath.suffix

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    for row in student_list:
        filename = [row[field] for field in name_fields]
        filename = "_".join(filename)

        filename = filename + "_" + base + suffix
        filename = filename.replace(" ", "_")  # remove any lingering spaces
        filename = filename.lower()

        # Copy file to new location
        shutil.copyfile(input_filepath, output_dir / filename)
