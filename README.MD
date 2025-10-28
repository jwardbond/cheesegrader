Cheesegrader 🧀
============

Cheesegrader is a CLI tool to streamline grading workflows for Quercus (Canvas). 

Its main features are: 
- `sorting`: Sorting rubrics/student assignments into folders based on their filenames. Useful to organize graders.
- `copying`: Generating a copy of a file for each student. Useful for rubrics.
- `renaming`: Replacing one id filenames with another id. Useful when (e.g.) you bulk download off quercus and find out the assignments don't have UTORID in the name.
- `downloading`: Downloading student lists, or assignment submissions.
- `uploading`: Uploading grades, files, or both to quercus for every student.


Following the prompts should be pretty straightforward, but you can press `h` at any time for help, and `q` or `ctrl+c` to quit.


## Table of contents<!-- omit from toc -->
- [Getting Started](#getting-started)
- [Authentication and tokens](#authentication-and-tokens)
- [Course and assignmend IDs](#course-and-assignmend-ids)
- [Contact](#contact)


## Getting Started
1. `pip install cheesegrader`
2. run `cheesegrader` from the command line
3. Follow the prompts
   

## Authentication and tokens
To use the uploading and downloading scripts, you will need to generate and input an API access token. You can get this:
- By following the instructions [here](https://developerdocs.instructure.com/services/canvas/oauth2/file.oauth#manual-token-generation)... but they were out of date last time I checked.
- Logging in to canvas/quercus and then `account > settings > + New Access Token`
- Navigating to [https://q.utoronto.ca/profile/settings](https://q.utoronto.ca/profile/settings) and clicking `+ New Access Token`


## Course and assignmend IDs
- Course and assignment IDs are visible in Quercus URLs:
  - https://q.utoronto.ca/courses/[COURSE_ID]/assignments/[ASSIGNMENT_ID]
- CSVs should have clean headers (no duplicates, no blanks) and UTF-8 encoding.


## Contact
- Submit issues/bugs [here](https://github.com/jwardbond/cheesegrader/issues)
- I'm also happy to answer any questions if you send them to jesse.wardbond at mail.utoronto.ca
// ...existing code...