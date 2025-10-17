import typer

from cheesegrader.cli import uploading, downloading, sorting, copying, token

app = typer.Typer(help="🧀 Cheesegrader CLI")

HELP_TEXT = """Help Menu:
    Enter the number corresponding to the module you want to run.
    ctrl+c to quit at any time.
    [0] Sorting: Organizes files into folders based on a student list. Useful for (e.g.) sorting rubrics/assignments by tutorial section.
    [1] Copying: Copies files and names them using a student list. Useful for (e.g.) copying a blank rubric for every student.
    [2] Uploading: Uploads grades and/or files to an assignment on Quercus.
    [3] Downloading: Downloads student lists from Quercus.\n
"""


@app.command()
def main():
    typer.secho(
        "Welcome to 🧀 Cheesegrader! ctrl+c to quit",
        fg=typer.colors.YELLOW,
        bold=True,
    )

    while True:
        typer.echo("Available modules: ")
        typer.echo("\t[0] Sorting")
        typer.echo("\t[1] Copying")
        typer.echo("\t[2] Uploading")
        typer.echo("\t[3] Downloading")
        typer.echo("\t[h] Help")

        choice = typer.prompt("What do you want to do?", type=str)
        typer.echo("\n")

        match choice:
            case "0":
                sorting.run()
                typer.Exit()
            case "1":
                copying.run()
                typer.Exit()
            case "2":
                tkn = token.ensure_token()
                uploading.run(tkn)
                typer.Exit()
            case "3":
                tkn = token.ensure_token()
                downloading.run(tkn)
                typer.Exit()
            case "h" | "H":
                typer.secho(HELP_TEXT, fg=typer.colors.YELLOW)
            case _:
                typer.secho("Invalid choice. Exiting.", fg=typer.colors.RED)
                typer.Exit()
