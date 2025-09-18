import pathlib
def file_lookup(idx: str, parent_paths: list[pathlib.Path]) -> list[pathlib.Path]:
    """Given an id and a list of parent paths, returns a list of files that match the id.

    Searches parent paths recursively.

    Args:
        idx (str): The id to search for in the file name
        parent_paths (list[pathlib.Path]): A list of parent paths to search for the id

    """
    output = []
    for path in parent_paths:
        try:
            matched_files = list(path.rglob(f"{idx}*"))
            output = output + matched_files
        except IndexError:
            continue
    return output



if __name__ == "__main__":
    print(file_lookup("barsaeli", [pathlib.WindowsPath('D:/OneDrive/School/PhD/ta/2024-esc203/grading/final_participation/OneDrive_2024-12-16/Batch #1 for Upload')]))
