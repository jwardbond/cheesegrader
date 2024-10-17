import os
import argparse
from pathlib import Path

import yaml

from src import QuercusCourse


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

    parser.add_argument("confpath", type=str, help="Path to config file")

    args = parser.parse_args()

    # Load config
    with open("./config.yml") as f:
        conf = yaml.safe_load(f)

    # Run scripts
    if args.upload:
        grade_file_path = Path(conf["grade_file_path"])
        folder_paths = [Path(f) for f in conf["additional_upload_paths"]]

        course = QuercusCourse(conf["course_id"], conf["auth_key"])
        course.upload_grades(
            conf["assignment_id"],
            grade_file_path,
            folder_paths,
        )

    elif args.students:
        course = QuercusCourse(conf["course_id"], conf["auth_key"])
        print(course.students)
        pass  # TODO finish implementation

    else:
        raise ValueError("Bad option")  # TODO takeout, probably don't need.


# @click.group(context_settings=CONTEXT_SETTINGS)
# @click.version_option(version='0.1.0', prog_name="hello")
# def control():
#     pass

# def dl_students():
#     print('dl-students')

#     course_id = CONFIG['course_id']
#     auth_key = TOKEN

#     course = QuercusCourse(course_id, auth_key)


#     print(f'Fetching student list for {course.get_course_title()}\n')

#     df = student_list.get_student_list_dataframe()
#     df.to_csv('quercus_student_list.csv', index=False)
