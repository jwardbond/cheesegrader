import shutil
from pathlib import Path
import zipfile


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


def sort_files(
    sort_dir: Path,
    dest_dir: Path,
    sort_map: dict[str, str],
) -> list[str]:
    """Sorts files into folders.

    Looks for files in `sort_dir` that match KEYS in `sort_map` and copies them
    into subfolders in `dest_dir` based on the corresponding VALUES in `sort_map`.

    Args:
        sort_dir (Path): The directory containing files to be sorted.
        dest_dir (Path): The base directory where sorted files will be placed.
        sort_map (dict[str, str]): A mapping of student identifiers to their corresponding
            destination subfolder names.

    Returns:
        list[str]: A list of filenames that were not found in the source directory.
    """
    missing_files = []

    for filename, subdir in sort_map.items():
        # Create output folder
        output_dir = dest_dir / subdir
        output_dir.mkdir(exist_ok=True, parents=True)

        # Find files that match
        matches = sort_dir.glob(f"*{filename}*")

        if not matches:
            missing_files.append(filename)

        for file in matches:
            shutil.copyfile(file, output_dir / file.name)

    return missing_files


def replace_filename_substr(input_dir: Path, rename_map: dict[str, str]) -> None:
    """Replaces portions of filenames in a directory based on a mapping.

    Useful when filenames contain an id number that needs to be replaced with another.

    Args:
        input_dir (Path): The directory containing files to be renamed.
        rename_map (dict[str, str]): A mapping of old substrings to new substrings for renaming.
    """
    for old_substr, new_substr in rename_map.items():
        for file in input_dir.glob(f"*{old_substr}*"):
            new_name = file.name.replace(old_substr, new_substr)
            new_path = input_dir / new_name
            file.rename(new_path)


def unzip_dir(input_file: Path) -> None:
    """Unzips a zip file to a directory.

    Args:
        input_file (Path): The zip file to be extracted.
    """
    output_dir = input_file.parent / (input_file.stem)

    with zipfile.ZipFile(input_file, "r") as zip_ref:
        zip_ref.extractall(output_dir)

    return output_dir
