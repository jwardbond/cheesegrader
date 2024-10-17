
# gradtools

## Setting up Gradtools

Run 
~~~console
pip install -r requirements.txt
~~~

Create a `config.yml` file. An example config file has been provided (`sample_config.yml`). The minimum possible data required is

~~~yaml
    # Your Canvas API authorization token, obtained by following: https://canvas.instructure.com/doc/api/file.oauth.html#manual-token-generation
    token: 

    # The course id, which you can obtain from the quercus url e.g. https://q.utoronto.ca/courses/[>= 6-digit number]
    course_id: 0
~~~

## Scripts

### `upload.py`

`upload.py` uploads PDF rubrics and grades to Quercus for a given assignment using Canvas APIs.

1. Prepare all rubrics in a single folder location. All rubrics must be named in a `UTORid_filename.pdf` format.
     >[!IMPORTANT] Team assignments
     > Team assignments are automatically detected by the program. These scripts only handle the case where everyone on the team gets the same grade. 
     >
     > For team assignments, replace `UTORID` with `TEAMID` (from quercus) in the rubric filenames.
2. Prepare a file with the grades.
   - The file must be a `.csv`
   - The first line of the file must have the header `id, grade`
   - Each line must contain `[id], [grade]`
3. Add the following to your `config.yml` file:
    ~~~yaml
        # The course id: you can obtain from the url: https://q.utoronto.ca/courses/[course_id]/assignments/[>= 6-digit number]
        assignment_id: 0,

        # Absolute path to the CSV file with the grades. 
        grade_file_path: "path/filename.csv",

        # OPTIONAL list of folders for containing additional grading files for upload (e.g. rubrics, marked-up assignments)
        # Files within these folders must have names starting with UTORid
        additional_upload_paths: ["path_to_folder_1", "path_to_folder_2"]
    ~~~

4. To upload rubrics, call

    ~~~console
    python upload.py <path-to-config-json>
    ~~~

## Downloading Assignments from Quercus
<https://q.utoronto.ca/api/v1/courses/{course_id}/students>
