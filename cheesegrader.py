import argparse
from pathlib import Path

import yaml

from src import QuercusCourse, copy_rename, filesorter

# TODO need to handle missing students better
# TODO need to add option to bulk rename files
# TODO extend api functionality to download assignments

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the various grading scripts available.",
    )

    # Flags for different grading tools
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-u",
        "--upload",
        action="store_true",
        help="Run the grade and file uploading script",
    )
    group.add_argument(
        "-s",
        "--students",
        action="store_true",
        help="Download as student list and save as csv",
    )
    group.add_argument(
        "-cr",
        "--copyrename",
        action="store_true",
        help="Copy a file and rename it according to a student list",
    )
    group.add_argument(
        "-o",
        "--sort",
        action="store_true",
        help="Sort named files by grader or section",
    )

    args = parser.parse_args()

    # Load config
    with open("./config.yml") as f:
        conf = yaml.safe_load(f)

    # Run whatever script was called
    if args.upload:
        # Get relevant data from config
        auth_key = conf["api"]["auth_key"]

        course_id = conf["api"]["course_id"]
        assignment_id = conf["api"]["upload"]["assignment_id"]

        grade_filepath = Path(conf["api"]["upload"]["grade_filepath"])
        folder_paths = [Path(f) for f in conf["api"]["upload"]["additional_upload_paths"]]

        mode = conf["api"]["upload"]["mode"]

        # Upload
        course = QuercusCourse(course_id, auth_key)
        course.upload(
            assignment_id,
            grade_filepath,
            mode,
            folder_paths,
        )

    elif args.students:
        # Get relevant data from config
        course_id = conf["api"]["course_id"]
        auth_key = conf["api"]["auth_key"]
        output_filepath = Path(conf["api"]["students"]["output_dir"]) / f"{course_id}_students.csv"

        # Download student list
        course = QuercusCourse(course_id, auth_key)
        course.generate_student_dataframe().to_csv(output_filepath, index=False)

        print(f"Generated student list at {output_filepath}")

    elif args.copyrename:
        # Get relevant data from config
        student_list = Path(conf["file_utils"]["student_list"])
        input_filepath = Path(conf["file_utils"]["copying"]["input_filepath"])
        output_dir = Path(conf["file_utils"]["copying"]["output_dir"])

        name_cols = conf["file_utils"]["copying"]["name_cols"]

        # Run
        copy_rename(student_list, input_filepath, output_dir, name_cols)

    elif args.sort:
        student_list = Path(conf["file_utils"]["student_list"])
        input_folder = Path(conf["file_utils"]["sorting"]["input_folder"])
        output_dir = Path(conf["file_utils"]["copying"]["output_dir"])

        sort_cols = conf["file_utils"]["sorting"]["sort_cols"]
        move = conf["file_utils"]["sorting"]["move"]
        id_col = conf["file_utils"]["sorting"]["id_col"]

        filesorter(student_list, input_folder, sort_cols, output_dir, move, id_col)

    else:
        msg = "Bad option"
        raise ValueError(msg)  # TODO takeout, probably don't need.
