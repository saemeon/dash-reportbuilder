# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Ensure SortableJS and the reportbuilder JS are available in the Dash app."""

from __future__ import annotations

import shutil
from importlib.resources import files
from pathlib import Path

import dash


def ensure_assets() -> None:
    """Copy SortableJS and reportbuilder JS into the running Dash app's assets.

    Safe to call multiple times — only copies if files are missing or outdated.
    Must be called after the Dash app is created.
    """
    pkg_assets = files("dash_reportbuilder") / "assets"
    app_assets = Path(dash.get_app().config.assets_folder)
    app_assets.mkdir(parents=True, exist_ok=True)

    for name in ("Sortable.min.js", "reportbuilder.js"):
        src = pkg_assets / name
        dst = app_assets / name
        # Copy if missing or if package version is newer
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            shutil.copy2(str(src), str(dst))
