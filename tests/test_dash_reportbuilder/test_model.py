# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

import pytest

from dash_reportbuilder.elements import (
    CaptionElement,
    HeadingElement,
    ImageElement,
    PageBreakElement,
    ParagraphElement,
)
from dash_reportbuilder.model import Report


def test_image_element_roundtrip():
    item = ImageElement(data_uri="data:image/png;base64,abc")
    d = item.to_dict()
    restored = ImageElement.from_dict(d)
    assert restored.id == item.id
    assert restored.data_uri == "data:image/png;base64,abc"


def test_report_append_remove():
    report = Report()
    item = HeadingElement(text="Hello", level=2)
    report.append(item)
    assert len(report.items) == 1
    report.remove(item.id)
    assert len(report.items) == 0


def test_report_reorder():
    report = Report()
    a = HeadingElement(text="A", level=2, id="aaa")
    b = ParagraphElement(text="B", id="bbb")
    c = ImageElement(data_uri="C", id="ccc")
    report.items = [a, b, c]

    report.reorder(["ccc", "aaa", "bbb"])
    assert [it.id for it in report.items] == ["ccc", "aaa", "bbb"]


def test_report_reorder_missing_ids():
    """Items not in the reorder list are appended at the end."""
    report = Report()
    a = HeadingElement(text="A", level=2, id="aaa")
    b = ParagraphElement(text="B", id="bbb")
    report.items = [a, b]

    report.reorder(["bbb"])
    assert [it.id for it in report.items] == ["bbb", "aaa"]


def test_report_update_item():
    report = Report()
    item = ParagraphElement(text="old", id="x")
    report.items = [item]
    report.update_item("x", text="new")
    assert report.items[0].text == "new"


def test_report_roundtrip():
    report = Report(title="Test Report")
    report.append(HeadingElement(text="Title", level=2))
    report.append(ImageElement(data_uri="data:image/png;base64,x"))

    d = report.to_dict()
    restored = Report.from_dict(d)
    assert restored.title == "Test Report"
    assert len(restored.items) == 2
    assert isinstance(restored.items[0], HeadingElement)
    assert isinstance(restored.items[1], ImageElement)


# --- Additional tests ---


class TestReportFromDictEdgeCases:
    """from_dict edge cases: missing fields, extra fields."""

    def test_missing_title_uses_default(self):
        data = {"items": []}
        report = Report.from_dict(data)
        assert report.title == "Untitled Report"

    def test_missing_items_uses_empty_list(self):
        data = {"title": "Report"}
        report = Report.from_dict(data)
        assert report.items == []

    def test_empty_dict(self):
        report = Report.from_dict({})
        assert report.title == "Untitled Report"
        assert report.items == []

    def test_extra_fields_ignored(self):
        data = {
            "title": "T",
            "items": [],
            "author": "Alice",
            "version": 42,
        }
        report = Report.from_dict(data)
        assert report.title == "T"
        assert report.items == []

    def test_unknown_type_raises(self):
        data = {"title": "T", "items": [{"id": "x", "type": "unknown_type"}]}
        with pytest.raises(ValueError):
            Report.from_dict(data)

    def test_full_roundtrip_preserves_all_types(self):
        """Every element type survives a to_dict/from_dict cycle."""
        report = Report(title="All Types")
        report.append(HeadingElement(text="H", level=2))
        report.append(ImageElement(data_uri="data:image/png;base64,x"))
        report.append(ParagraphElement(text="P"))
        report.append(CaptionElement(text="C"))
        report.append(PageBreakElement())

        restored = Report.from_dict(report.to_dict())
        assert len(restored.items) == 5
        for orig, rest in zip(report.items, restored.items, strict=True):
            assert type(orig) is type(rest)


class TestReportEmptyTitle:
    """Report with empty-string title."""

    def test_empty_title(self):
        report = Report(title="")
        assert report.title == ""
        d = report.to_dict()
        assert d["title"] == ""

    def test_empty_title_roundtrip(self):
        report = Report(title="")
        restored = Report.from_dict(report.to_dict())
        assert restored.title == ""


class TestReorderEdgeCases:
    """Edge cases for reorder."""

    def test_reorder_with_duplicate_ids(self):
        """Duplicate IDs in the reorder list: each ID maps to one item."""
        report = Report()
        a = HeadingElement(text="A", level=2, id="aaa")
        b = ParagraphElement(text="B", id="bbb")
        report.items = [a, b]

        report.reorder(["aaa", "aaa", "bbb"])
        ids = [it.id for it in report.items]
        assert ids.count("aaa") == 1
        assert ids.count("bbb") == 1
        assert ids[0] == "aaa"

    def test_reorder_empty_list(self):
        """Empty reorder list: all items are appended as 'not in list'."""
        report = Report()
        a = HeadingElement(text="A", level=2, id="aaa")
        b = ParagraphElement(text="B", id="bbb")
        report.items = [a, b]
        report.reorder([])
        assert [it.id for it in report.items] == ["aaa", "bbb"]

    def test_reorder_unknown_ids_ignored(self):
        """IDs in the reorder list that don't exist are silently skipped."""
        report = Report()
        a = HeadingElement(text="A", level=2, id="aaa")
        report.items = [a]
        report.reorder(["zzz", "aaa", "yyy"])
        assert [it.id for it in report.items] == ["aaa"]

    def test_reorder_on_empty_report(self):
        report = Report()
        report.reorder(["aaa", "bbb"])
        assert report.items == []


class TestUpdateAndRemoveEdgeCases:
    """update_item and remove with nonexistent IDs."""

    def test_update_nonexistent_id_is_noop(self):
        report = Report()
        item = ParagraphElement(text="original", id="x")
        report.items = [item]
        report.update_item("nonexistent", text="new text")
        assert report.items[0].text == "original"

    def test_update_empty_report(self):
        report = Report()
        report.update_item("any", text="text")
        assert report.items == []

    def test_remove_nonexistent_id_is_noop(self):
        report = Report()
        item = HeadingElement(text="H", level=2, id="x")
        report.items = [item]
        report.remove("nonexistent")
        assert len(report.items) == 1
        assert report.items[0].id == "x"

    def test_remove_from_empty_report(self):
        report = Report()
        report.remove("any")
        assert report.items == []

    def test_remove_same_id_twice(self):
        report = Report()
        item = HeadingElement(text="H", level=2, id="x")
        report.items = [item]
        report.remove("x")
        report.remove("x")
        assert report.items == []


class TestReportAppendMultiple:
    """Append multiple items and verify ordering."""

    def test_append_preserves_order(self):
        report = Report()
        for i in range(5):
            report.append(ParagraphElement(text=str(i), id=f"id{i}"))
        assert [it.id for it in report.items] == [f"id{i}" for i in range(5)]

    def test_to_dict_preserves_item_order(self):
        report = Report()
        report.append(HeadingElement(text="first", level=2, id="a"))
        report.append(ParagraphElement(text="second", id="b"))
        d = report.to_dict()
        assert d["items"][0]["id"] == "a"
        assert d["items"][1]["id"] == "b"


class TestElementId:
    """Auto-generated ID behaviour."""

    def test_auto_id_is_12_hex(self):
        item = HeadingElement(text="H", level=2)
        assert len(item.id) == 12
        int(item.id, 16)

    def test_explicit_id(self):
        item = HeadingElement(text="H", level=2, id="my-custom-id")
        assert item.id == "my-custom-id"

    def test_unique_ids(self):
        ids = {HeadingElement(text="H", level=2).id for _ in range(100)}
        assert len(ids) == 100


class TestUnicodeContent:
    """Content with unicode characters round-trips cleanly."""

    def test_unicode_text(self):
        item = ParagraphElement(text="Hello—world éèê")
        d = item.to_dict()
        restored = ParagraphElement.from_dict(d)
        assert restored.text == "Hello—world éèê"
