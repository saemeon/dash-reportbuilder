# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Integration with dash-capture: provides a WizardAction for adding captures to reports."""

from __future__ import annotations

from typing import Any

# Global version counters per store — bumped on every mutation so the
# viewer knows to refresh.  WeakKeyDictionary avoids id() collisions when
# a store is garbage-collected and the next allocation reuses its id.
from weakref import WeakKeyDictionary

from dash_capture import WizardAction

from dash_reportbuilder.elements import ImageElement
from dash_reportbuilder.store import ReportStore

_version_counters: WeakKeyDictionary[ReportStore, int] = WeakKeyDictionary()


def _bump_version(store: ReportStore) -> int:
    _version_counters[store] = _version_counters.get(store, 0) + 1
    return _version_counters[store]


def get_version(store: ReportStore) -> int:
    """Return the current mutation version for *store*."""
    return _version_counters.get(store, 0)


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
        item = ImageElement(
            data_uri=data_uri,
            title=kwargs.get("title"),
            caption=kwargs.get("caption"),
            width_mm=kwargs.get("width_mm"),
        )
        report = store.get(session_id)
        report.add(item)
        store.put(session_id, report)
        _bump_version(store)

    return WizardAction(label=label, callback=_on_capture)
