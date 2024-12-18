import pathlib
import shutil

import pandas as pd


def copy_rename(
    student_list: pathlib.Path,
    input_filepath: pathlib.Path,
    output_dir: pathlib.Path | None = None,
    name_cols: list[int] | None = None,
) -> None:
    """Copies a file and renames it according to user-specified columns in a class .csv file.

    This function reads a CSV file containing student information, and for each student,
    it copies a specified input file to a designated output directory, renaming the file
    based on the values from specified columns in the CSV.

    Args:
        student_list (pathlib.Path): A path to a CSV file containing student data.
        input_filepath (pathlib.Path): A path to a file that needs to be copied.
        output_dir (pathlib.Path, optional): A directory where the copied files will be saved.
            If not provided, the output will be saved in the same directory as the input file.
        name_cols (list, optional): A list of column indices or names from the CSV to use for
            generating the new filenames. If empty, the first column value will be used.

    Raises:
        FileNotFoundError: #TODO
    """
    student_df = pd.read_csv(student_list)

    # Get base filename
    base = input_filepath.stem  # TODO allow users to optionally define names
    ext = input_filepath.suffix

    # Make sure output_dir exists
    if output_dir:
        output_dir.mkdir(exist_ok=True)
    else:
        output_dir = input_filepath.parent

    for row in student_df.iterrows():
        # Create filename
        if name_cols:
            filename = [row[1].iloc[x] for x in name_cols]
            filename = "_".join(filename)
        else:
            filename = row[1].iloc[0]

        filename = filename + "_" + base + ext
        filename = filename.replace(" ", "_")  # remove any lingering spaces
        filename = filename.lower()

        # Copy file to new location
        shutil.copyfile(input_filepath, output_dir / filename)


def filesorter(
    student_list: pathlib.Path,
    input_folder: pathlib.Path,
    sort_cols: list,
    output_dir: pathlib.Path,
    move: bool,
    id_col: int,
) -> list[str]:
    """Sorts files into folders based on student identifiers from a CSV file.

    Reads a list of students from a CSV file and searches for files in the specified
    input folder that match the identifiers of each student. Files are organized into
    subfolders created based on specified columns in the student data, with options to
    either copy or move the files.

    Args:
        student_list (pathlib.Path): Path to the CSV file containing student data.
        input_folder (pathlib.Path): Path to the folder where files to be sorted are located.
        sort_cols (list): List of indices or column names used to create the output folder names.
        output_dir (pathlib.Path, optional): Directory where sorted folders should be created.
            If not provided, output folders will be created within the input folder.
        move (bool, optional): If True, files will be moved; if False, files will be copied.
            Defaults to False (copying file).
        id_col (int, optional): Index of the column that contains student identifiers. Defaults
            to 0 (leftmost column).

    Returns:
        missing_students: A list of student identifiers for which no matching files were found in the
            input folder.
    """
    student_df = pd.read_csv(student_list)

    missing_students = []
    for row in student_df.iterrows():
        # Create output folder
        output_folder = [str(row[1].iloc[x]) for x in sort_cols]
        output_folder = output_dir / "/".join(output_folder)
        output_folder.mkdir(exist_ok=True)

        # Find files that match
        idx = row[1].iloc[id_col]
        matches = input_folder.glob(f"*{idx}*")

        if not matches:
            missing_students.append(idx)

        for file in matches:
            if move:
                shutil.move(input_folder / file, output_folder / file)
            else:
                shutil.copyfile(input_folder / file, output_folder / file)

    return missing_students
