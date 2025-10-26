import typer

from cheesegrader.cli import copying, downloading, sorting, token, uploading
from cheesegrader.cli.utils import create_prompt

app = typer.Typer(help="🧀 Cheesegrader CLI")

HELP_TEXT = """
Help Menu:
    Enter the number corresponding to the module you want to run.
    [0] Sorting: Organizes files into folders based on a student list. Useful for (e.g.) sorting rubrics/assignments by tutorial section.
    [1] Copying: Copies files and names them using a student list. Useful for (e.g.) copying a blank rubric for every student.
    [2] Uploading: Uploads grades and/or files to an assignment on Quercus.
    [3] Downloading: Downloads student lists from Quercus.

    ---
    Enter 'q' or press ctrl+c to quit at any time.
    Enter 'h' for help."""


@app.command()
def main() -> None:
    typer.secho(
        "Welcome to 🧀 Cheesegrader! ctrl+c to quit",
        fg=typer.colors.YELLOW,
        bold=True,
    )
    main_menu()


prompt = create_prompt(HELP_TEXT)


def main_menu() -> None:
    while True:
        typer.echo()
        typer.echo("Available modules: ")
        typer.echo("\t[0] Sorting")
        typer.echo("\t[1] Copying")
        typer.echo("\t[2] Uploading")
        typer.echo("\t[3] Downloading")
        typer.echo("\t---")
        typer.echo("\t[h] Help")
        typer.echo("\t[q] Quit")

        choice = prompt("What do you want to do?", type=str)

        match choice:
            case "0":
                sorting.run()
            case "1":
                copying.run()
            case "2":
                token.ensure_token()
                uploading.run()
            case "3":
                token.ensure_token()
                downloading.run()
