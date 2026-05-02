# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

from dash_capture import WizardAction

from dash_reportbuilder.capture import _bump_version, get_version, report_action
from dash_reportbuilder.elements import ImageElement
from dash_reportbuilder.store import MemoryStore


def test_report_action_returns_wizard_action():
    store = MemoryStore()
    action = report_action(store)
    assert isinstance(action, WizardAction)
    assert action.label == "Add to Report"


def test_report_action_callback_appends_item():
    store = MemoryStore()
    action = report_action(store, session_id="test")

    action.callback("data:image/png;base64,abc123")

    report = store.get("test")
    assert len(report.items) == 1
    item = report.items[0]
    assert isinstance(item, ImageElement)
    assert item.data_uri == "data:image/png;base64,abc123"


def test_report_action_callback_passes_kwargs_as_attributes():
    store = MemoryStore()
    action = report_action(store, session_id="test")

    action.callback("data:image/png;base64,x", caption="Chart 1", title="Foo")

    item = store.get("test").items[0]
    assert item.title == "Foo"
    assert item.caption == "Chart 1"


def test_report_action_callback_filters_none_kwargs():
    store = MemoryStore()
    action = report_action(store, session_id="test")

    action.callback("data:image/png;base64,x", caption=None, title="Foo")

    item = store.get("test").items[0]
    assert item.title == "Foo"
    assert item.caption is None


def test_version_counter():
    store = MemoryStore()
    v0 = get_version(store)
    _bump_version(store)
    v1 = get_version(store)
    assert v1 == v0 + 1


def test_report_action_bumps_version():
    store = MemoryStore()
    action = report_action(store, session_id="test")
    v0 = get_version(store)

    action.callback("data:image/png;base64,x")

    v1 = get_version(store)
    assert v1 > v0


def test_report_action_custom_label():
    store = MemoryStore()
    action = report_action(store, label="Save Chart")
    assert action.label == "Save Chart"


def test_report_action_default_session():
    """Default session_id is 'default'."""
    store = MemoryStore()
    action = report_action(store)
    action.callback("data:image/png;base64,abc")
    report = store.get("default")
    assert len(report.items) == 1


def test_report_action_multiple_captures():
    store = MemoryStore()
    action = report_action(store, session_id="multi")
    for i in range(5):
        action.callback(f"data:image/png;base64,img{i}")

    report = store.get("multi")
    assert len(report.items) == 5
    for i, item in enumerate(report.items):
        assert isinstance(item, ImageElement)
        assert item.data_uri == f"data:image/png;base64,img{i}"


def test_version_independent_per_store():
    """Each store has its own version counter."""
    store_a = MemoryStore()
    store_b = MemoryStore()
    va0 = get_version(store_a)
    vb0 = get_version(store_b)
    _bump_version(store_a)
    _bump_version(store_a)
    _bump_version(store_b)
    assert get_version(store_a) == va0 + 2
    assert get_version(store_b) == vb0 + 1


def test_version_starts_at_zero():
    store = MemoryStore()
    assert get_version(store) == 0


def test_bump_version_returns_new_value():
    store = MemoryStore()
    v = _bump_version(store)
    assert v == 1
    v = _bump_version(store)
    assert v == 2


def test_callback_preserves_item_order():
    store = MemoryStore()
    action = report_action(store, session_id="order")
    action.callback("data:image/png;base64,first")
    action.callback("data:image/png;base64,second")
    report = store.get("order")
    assert report.items[0].data_uri == "data:image/png;base64,first"
    assert report.items[1].data_uri == "data:image/png;base64,second"
