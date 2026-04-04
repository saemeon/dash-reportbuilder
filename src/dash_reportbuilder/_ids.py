# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

import secrets


def _new_id(prefix: str = "") -> str:
    """Generate a unique Dash component ID for dash-reportbuilder internals."""
    token = secrets.token_hex(4)
    return f"_drb_{prefix}_{token}" if prefix else f"_drb_{token}"
