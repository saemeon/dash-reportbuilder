# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Server-side report storage backends."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Protocol, runtime_checkable

from dash_reportbuilder.model import Report


@runtime_checkable
class ReportStore(Protocol):
    """Protocol for report storage backends."""

    def get(self, session_id: str) -> Report: ...
    def put(self, session_id: str, report: Report) -> None: ...
    def delete(self, session_id: str) -> None: ...


class MemoryStore:
    """In-memory report store backed by a dict.

    Suitable for development and single-process deployments.
    Thread-safe via per-session locking.
    """

    def __init__(self) -> None:
        self._reports: dict[str, Report] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str) -> Report:
        with self._lock:
            if session_id not in self._reports:
                self._reports[session_id] = Report()
            return self._reports[session_id]

    def put(self, session_id: str, report: Report) -> None:
        with self._lock:
            self._reports[session_id] = report

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._reports.pop(session_id, None)


class FileStore:
    """File-based report store.

    Each session is stored as a JSON file.  Suitable for single-server
    production deployments where persistence across restarts is needed.

    Parameters
    ----------
    directory : str or Path, optional
        Directory for report files.  Defaults to a temp directory.
    """

    def __init__(self, directory: str | Path | None = None) -> None:
        if directory is None:
            import tempfile

            directory = Path(tempfile.mkdtemp(prefix="dash_report_"))
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, session_id: str) -> Path:
        # Sanitise session_id to prevent path traversal
        safe_id = session_id.replace("/", "_").replace("..", "_")
        return self._dir / f"{safe_id}.json"

    def get(self, session_id: str) -> Report:
        path = self._path(session_id)
        with self._lock:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                return Report.from_dict(data)
            return Report()

    def put(self, session_id: str, report: Report) -> None:
        path = self._path(session_id)
        with self._lock:
            path.write_text(
                json.dumps(report.to_dict(), ensure_ascii=False),
                encoding="utf-8",
            )

    def delete(self, session_id: str) -> None:
        path = self._path(session_id)
        with self._lock:
            path.unlink(missing_ok=True)
