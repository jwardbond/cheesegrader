import typer

from cheesegrader.cli import uploading, downloading, sorting, copying, token

app = typer.Typer(help="🧀 Cheesegrader CLI")


@app.command()
def main():
    typer.secho(
        "Welcome to 🧀 Cheesegrader! Enter 'q' or ctrl+c to quit",
        fg=typer.colors.YELLOW,
        bold=True,
    )
    typer.echo("Modules?")
    typer.echo("\t[0] Sorting")
    typer.echo("\t[1] Copying")
    typer.echo("\t[2] Uploading")
    typer.echo("\t[3] Downloading")

    choice = typer.prompt("What do you want to do?", type=int)

    if choice == 0:
        sorting.run()
    elif choice == 1:
        copying.run()
    elif choice == 2:
        token.ensure_token()
        uploading.run()
    elif choice == 3:
        token.ensure_token()
        downloading.run()
    else:
        typer.secho("Invalid choice. Exiting.", fg=typer.colors.RED)
