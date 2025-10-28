# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond
"""Quercus Token API Tools.

This module provides functions for validating and managing authentication tokens
for accessing the Canvas/Quercus LMS API.

Functions:
    token_is_valid: Checks if a given token is valid.
    get_user_id_from_token: Retrieves the user ID associated with a given token.
"""

import requests as r

CANVAS_API_BASE = "https://canvas.instructure.com/api/v1/users/self"


def token_is_valid(token: str) -> bool:
    """Return True if the token is valid, False otherwise."""
    headers = {"Authorization": f"Bearer {token}"}
    response = r.get(CANVAS_API_BASE, headers=headers, timeout=10)

    return response.ok


def get_user_from_token(token: str) -> dict:
    """Get the user information associated with a token.

    Args:
        token (str): The authentication token.

    Raises:
        ValueError: If the token is invalid.

    Returns:
        dict | None: The user information if retrieval is successful, None otherwise.
    """
    headers = {"Authorization": f"Bearer {token}"}
    response = r.get(CANVAS_API_BASE, headers=headers, timeout=10)

    if not token_is_valid(token):
        msg = "Invalid token provided."
        raise ValueError(msg)

    return response.json()
