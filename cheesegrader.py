import os
import argparse
from pathlib import Path

import yaml

from src import QuercusCourse, copy_rename, filesorter


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the various grading scripts available."
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

    # parser.add_argument("confpath", type=str, help="Path to config file")

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

        grade_file_path = Path(conf["api"]["upload"]["grade_file_path"])
        folder_paths = [
            Path(f) for f in conf["api"]["upload"]["additional_upload_paths"]
        ]

        # Upload
        course = QuercusCourse(course_id, auth_key)
        course.upload_grades(
            assignment_id,
            grade_file_path,
            folder_paths,
        )

    elif args.students:
        # Get relevant data from config
        course_id = conf["api"]["course_id"]
        auth_key = conf["api"]["auth_key"]
        output_dir = Path(conf["api"]["students"]["output_dir"])

        # Download student list
        course = QuercusCourse(course_id, auth_key)
        output_filepath = output_dir / f"{course_id}_stusdent_list.csv"
        course.generate_student_dataframe().to_csv(output_filepath, index=False)

        print(f"Generated student list at {output_filepath}")

    elif args.copyrename:
        # Get relevant data from config
        student_list = Path(conf["file_utils"]["student_list"])
        input_filepath = Path(conf["file_utils"]["copying"]["input_filepath"])
        if conf["file_utils"]["copying"]["output_dir"]:
            output_dir = Path(conf["file_utils"]["copying"]["output_dir"])
        else:
            output_dir = None

        name_cols = conf["file_utils"]["copying"]["name_cols"]

        # Run
        copy_rename(student_list, input_filepath, output_dir, name_cols)

    elif args.sort:
        student_list = Path(conf["file_utils"]["student_list"])
        input_folder = Path(conf["file_utils"]["sorting"]["input_folder"])
        sort_cols = conf["file_utils"]["sorting"]["input_folder"]
        # output_dir =
        # move =

    else:
        raise ValueError("Bad option")  # TODO takeout, probably don't need.
