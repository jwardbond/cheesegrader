
# Cheesegrader

- [Cheesegrader](#cheesegrader)
  - [Setting up Cheesegrader](#setting-up-cheesegrader)
  - [Config](#config)
  - [Examples](#examples)
    - [Downloading student lists](#downloading-student-lists)
    - [Uploading grades](#uploading-grades)
    - [Generating copies (and other files)](#generating-copies-and-other-files)
    - [Sorting files](#sorting-files)
  - [Contact](#contact)

## Setting up Cheesegrader
<a name="setup"></a>

1. Download this repository off github, or clone it into your grading directory
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
        course_id: 0123456
~~~

Every command requires you to fill out some associated info in `config.yml`. Refer to the sections below, and to the information given in `sample_config.yml`

>[!IMPORTANT]
> You can get your API authorization token by following the instructions here: https://canvas.instructure.com/doc/api/file.oauth.html#manual-token-generation. Which basically tells you to go to `quercus > account > settings > approved integrations`   

## Examples
### Downloading student lists
<a name="s"></a>
Cheesegrader can be used to generate student lists that include internal quercus ids, as well as utorids. This is useful when downloading assignments off of quercus. To use:
1. Fill out the `api > students` section in `config.yml`

2. Run `python cheesegrader.py -s`

### Uploading grades
<a name="u"></a>

Cheesegrader can be used to upload grades and other marking documents (rubrics, mark-ups) for a given assignment. This can be done on a per-group or per-student basis. To use:

1. Prepare all rubrics in a single folder location. All rubrics must be named in a `UTORid_filename.pdf` format.


2. Prepare a file with the grades.
   - The file must be a `.csv`
   - The first line of the file must have the header `id, grade`
   - Each line must contain `[id], [grade]`
3. Fill out the `api > upload` section of config.yml`


4. Run `python cheesegrader.py -u` and follow the prompts

> [!NOTE]
> Uploading files
> 
> You can use `additional_upload_paths` in `config.yml` to include folders containing files you want to upload. This is useful when you have (e.g.) rubrics or marked-up assignments that you want to hand back. The files in these folders must have the `UTORid` (or `TEAMid`) somewhere in their name.

>[!NOTE]
> Team assignments
>
> Team assignments are automatically detected by the program. These scripts only handle the case where everyone on the team gets the same grade. 
>
> For team assignments, replace `UTORid` with `TEAMid` (from quercus) in the rubric filenames.

### Generating copies (and other files)
<a name="cr"></a>

Cheesegrader can be used generate copies of a single file for every student in a course. This is useful when you want to generate (e.g.) rubrics. To do this:

1. Fill out the `file_utils > copying` section of `config.yml`
2. Run `python cheesegrader.py -cr`

>[!NOTE]
> `name_cols`
> 
> The file you copy will have additional names prepended to it, e.g. "rubric.pdf" becomes "129039_jesse_rubric.pdf". Use `name_cols` to indicate which columns in your student list contain the information you want to add. 

### Sorting files
<a name="o"></a>

Cheesegrader can be used to sort class files into folders. This is useful when (e.g.) you have just created a bunch of rubrics or downloaded a bunch of assignments, and want to sort them by assigned marker. To do this:

1. Fill out the `file_utils > sorting` section of `config.yml`
2. Run `python cheesegrader.py -o`
   
>[!NOTE]
> This program will automatically create subfolders in your specified `output_dir`. If you want to have more than one level of subfolders (e.g. one folder per TA, followed by one folder for each section that TA is marking) specify the additional levels using `sort_cols`. 
>
>This creates the folder hierarchy left-to-right through the list. For instance `sort_cols:[4,0]` would first create one folder for whatever is in column 0 of your student list, and then create *sub* folders using whatever is in column 4.

## Contact
This is very much in beta. If you need some help please reach out to me at jesse.wardbond at mail.utoronto.ca