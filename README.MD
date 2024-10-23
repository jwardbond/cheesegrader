
# Cheesegrader

- [Cheesegrader](#cheesegrader)
  - [Setting up Cheesegrader](#setting-up-cheesegrader)
  - [Config](#config)
  - [Examples](#examples)
    - [Downloading student lists](#downloading-student-lists)
    - [Uploading grades](#uploading-grades)
    - [Generating Rubrics (and other files)](#generating-rubrics-and-other-files)
    - [Downloading Assignments from Quercus](#downloading-assignments-from-quercus)

## Setting up Cheesegrader
<a name="setup"></a>

1. Download these repository off github, or clone it into your grading directory
2. Run `pip install -r requirements.txt` to install everything you need
3. Create a `config.yml` file (see below)

## Config
<a name="config"></a>

Cheesegrader uses a `config.yml` file to control everything.  An example config file has been provided (`sample_config.yml`). If you want to use it to interact with quercus APIs, then this file needs to contain, at minimum:

~~~yaml
    api:
        # Your Canvas API authorization token 
        token: "somerandomstringthatisreallylongandfullofnumberslike123123121809132andsymbols$%#$%#$%"

        # The course id, which you can obtain from the quercus url e.g. https://q.utoronto.ca/courses/[>= 6-digit number]
        course_id: 0
~~~

>[!IMPORTANT]
> You can get your API authorization token by following the instructions here: https://canvas.instructure.com/doc/api/file.oauth.html#manual-token-generation. Which basically tells you to go to `quercus > account > settings > approved integrations`   

## Examples
### Downloading student lists
<a name="s"></a>
Cheesegrader can be used to generate student lists that include internal quercus ids, as well as utorids. This is useful when downloading assignments off of quercus. To use:
1. Add the following line to your `config.yml` file:
    
    ~~~yaml
        output_dir: "path"
    ~~~

2. Run `python cheesegrader -s`

### Uploading grades
<a name="u"></a>

Cheesegrader can be used to upload grades and other marking documents (rubrics, mark-ups) for a given assignment. This can be done on a per-group or per-student basis. To use:

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
        api:
            token: "somerandomstringthatisreallylongandfullofnumberslike123123121809132andsymbols$%#$%#$%"
            course_id: 0
            upload:
                # The course id: you can obtain from the url: https://q.utoronto.ca/courses/[course_id]/assignments/[>= 6-digit number]
                assignment_id: 0

                # Absolute path to the CSV file with the grades. 
                grade_file_path: "path/filename.csv"

                # OPTIONAL list of folders for containing additional grading files for upload (e.g. rubrics, marked-up assignments)
                # Files within these folders must have names starting with UTORid
                additional_upload_paths: ["path_to_folder_1", "path_to_folder_2"]
    ~~~

4. Run `python cheesegrader -u` and follow the prompts

### Generating Rubrics (and other files)


### Downloading Assignments from Quercus
tbd
