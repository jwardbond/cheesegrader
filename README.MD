Cheesegrader 🧀
============

Cheesegrader is a CLI tool to streamline grading workflows for Quercus (Canvas). Its main features are

Interacting with quercus programmatically: 
- `downloading` student lists and student submissions
- `uploading` grades, files, or both
- `deleting` comments for a given assignment (useful if you've messed up during uploading)

Convenient file utils:
- `sorting` files into folders (e.g., sorting assignment submissions by graders)
- `copying`: Copy and rename a file (e.g., creating a named copy of a rubric for every student in a course)
- `renaming`: Bulk replace part of a named file with another name (e.g., replacing quercus IDs with UTORID)

Following the prompts should be pretty straightforward, but you can press `h` at any time for help, and `q` or `ctrl+c` to quit.


## Table of contents<!-- omit from toc -->
- [Getting Started](#getting-started)
- [Authentication and tokens](#authentication-and-tokens)
- [Course and assignment IDs](#course-and-assignment-ids)
- [Todo](#todo)
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


## Course and assignment IDs
- Course and assignment IDs are visible in Quercus URLs:
  - https://q.utoronto.ca/courses/[COURSE_ID]/assignments/[ASSIGNMENT_ID]
- CSVs should have clean headers (no duplicates, no blanks) and UTF-8 encoding.


## Todo
- Implement group assignments
- Multithread uploads


## Contact
- Submit issues/bugs [here](https://github.com/jwardbond/cheesegrader/issues)
- I'm also happy to answer any questions if you send them to jesse.wardbond at mail.utoronto.ca