# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Jesse Ward-Bond
"""Quercus Token API Tools.

This module provides functions for validating and managing authentication tokens
for accessing the Canvas/Quercus LMS API.

Functions:
    validate_token: Validates a given authentication token.
"""

import requests as r

CANVAS_API_BASE = "https://canvas.instructure.com/api/v1"


def validate_token(token: str) -> bool:
    """Return True if the token is valid, False otherwise."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = r.get(f"{CANVAS_API_BASE}/courses", headers=headers, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"Token validation failed: {response.status_code} {response.text}")
            return False
    except r.RequestException as e:
        print(f"Error validating token: {e}")
        return False
