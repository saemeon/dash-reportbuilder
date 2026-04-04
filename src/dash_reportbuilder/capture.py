# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Integration with dash-capture: provides a WizardAction for adding captures to reports."""

from __future__ import annotations

from typing import Any

from dash_capture import WizardAction

from dash_reportbuilder.model import ItemType, ReportItem
from dash_reportbuilder.store import ReportStore

# Global version counters per store — bumped on every mutation so the
# viewer knows to refresh.  Keyed by id(store).
_version_counters: dict[int, int] = {}


def _bump_version(store: ReportStore) -> int:
    key = id(store)
    _version_counters[key] = _version_counters.get(key, 0) + 1
    return _version_counters[key]


def get_version(store: ReportStore) -> int:
    """Return the current mutation version for *store*."""
    return _version_counters.get(id(store), 0)


def report_action(
    store: ReportStore,
    session_id: str = "default",
    label: str = "Add to Report",
) -> WizardAction:
    """Create a :class:`~dash_capture.WizardAction` that appends captures to a report.

    Parameters
    ----------
    store : ReportStore
        The report store to append items to.
    session_id : str
        Session identifier.  In a multi-user app, wire this to a
        per-tab ``dcc.Store`` value instead of using the default.
    label : str
        Button label shown in the capture wizard.

    Returns
    -------
    WizardAction
        Pass this to ``capture_graph(actions=[...])`` or
        ``capture_element(actions=[...])``.
    """

    def _on_capture(data_uri: str, **kwargs: Any) -> None:
        meta = {k: v for k, v in kwargs.items() if v is not None}
        item = ReportItem(type=ItemType.IMAGE, content=data_uri, meta=meta)
        report = store.get(session_id)
        report.append(item)
        store.put(session_id, report)
        _bump_version(store)

    return WizardAction(label=label, callback=_on_capture)
