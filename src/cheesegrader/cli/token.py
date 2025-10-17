import typer
from pathlib import Path
import json
from cheesegrader.api_tools import validate_token

TOKEN_FILE = Path.home() / ".cheesegrader_token"


def ensure_token() -> str:
    """Prompt for token if not stored, validate, and persist."""

    use_saved = False
    token = None

    if TOKEN_FILE.exists():
        use_saved = typer.confirm(
            f"A saved token was found at {TOKEN_FILE}. Do you want to use it?",
            default=True,
        )

        token = load_token() if use_saved else None

    if not token:
        typer.echo("No saved token found.")
        token = typer.prompt("Enter your API token")

    typer.echo("Validating token...")
    if not validate_token(token):
        typer.secho("Invalid token.", fg=typer.colors.RED)
        typer.echo(
            "You can get a token from your account page by following the instructions: https://developerdocs.instructure.com/services/canvas/oauth2/file.oauth#manual-token-generation"
        )
        return ensure_token()

    typer.secho("Token validated.", fg=typer.colors.GREEN)

    if not use_saved:
        save_new = typer.confirm(
            "Do you want to save this token for future use?", default=True
        )
        if save_new:
            save_token(token)

    return token


def load_token() -> str | None:
    if TOKEN_FILE.exists():
        try:
            return json.loads(TOKEN_FILE.read_text()).get("token")
        except json.JSONDecodeError:
            return None
    return None


def save_token(token: str):
    typer.echo(f"Saving token to {TOKEN_FILE}")
    TOKEN_FILE.write_text(json.dumps({"token": token}))


def delete_token():
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
