import json
import os
from pathlib import Path

import typer

from cheesegrader.api_tools import validate_token
from cheesegrader.cli.utils import SUCCESS_FG, create_confirm, create_prompt

TOKEN_FILE = Path.home() / ".cheesegrader_token"
TOKEN_VAR_NAME = "CG_TOKEN"

HELP_MSG = "TBD"  # TODO

prompt = create_prompt(HELP_MSG)
confirm = create_confirm(HELP_MSG)


def ensure_token() -> str:
    """Prompt for token if not stored, validate, and persist."""
    use_saved = False
    token = None

    if TOKEN_FILE.exists():
        typer.echo(f"A saved token was found at {TOKEN_FILE}.")
        use_saved = confirm("Use saved token?")

        token = load_token() if use_saved else None

    if not token:
        typer.echo("No saved token found.")
        token = typer.prompt("Enter your API token")

    typer.echo("Validating token...")
    if not validate_token(token):
        typer.secho("Invalid token.", fg=typer.colors.RED)
        typer.echo(
            "You can get a token from your account page by following the instructions: https://developerdocs.instructure.com/services/canvas/oauth2/file.oauth#manual-token-generation",
        )
        return ensure_token()

    typer.secho("Token validated.", fg=typer.colors.GREEN)

    if not use_saved:
        save_new = confirm("Do you want to save this token for future use?", default=True)
        if save_new:
            save_token(token)

    # Load into env
    os.environ[TOKEN_VAR_NAME] = token
    return None


def load_token() -> str | None:
    if TOKEN_FILE.exists():
        try:
            return json.loads(TOKEN_FILE.read_text()).get("token")
        except json.JSONDecodeError:
            return None
    return None


def save_token(token: str):
    typer.secho(f"Saved token to {TOKEN_FILE}", fg=SUCCESS_FG)
    TOKEN_FILE.write_text(json.dumps({"token": token}))


def delete_token():
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
