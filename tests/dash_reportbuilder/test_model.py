# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

from dash_reportbuilder.model import ItemType, Report, ReportItem


def test_report_item_roundtrip():
    item = ReportItem(type=ItemType.IMAGE, content="data:image/png;base64,abc")
    d = item.to_dict()
    restored = ReportItem.from_dict(d)
    assert restored.id == item.id
    assert restored.type == ItemType.IMAGE
    assert restored.content == "data:image/png;base64,abc"


def test_report_append_remove():
    report = Report()
    item = ReportItem(type=ItemType.HEADING, content="Hello")
    report.append(item)
    assert len(report.items) == 1
    report.remove(item.id)
    assert len(report.items) == 0


def test_report_reorder():
    report = Report()
    a = ReportItem(type=ItemType.HEADING, content="A", id="aaa")
    b = ReportItem(type=ItemType.PARAGRAPH, content="B", id="bbb")
    c = ReportItem(type=ItemType.IMAGE, content="C", id="ccc")
    report.items = [a, b, c]

    report.reorder(["ccc", "aaa", "bbb"])
    assert [it.id for it in report.items] == ["ccc", "aaa", "bbb"]


def test_report_reorder_missing_ids():
    """Items not in the reorder list are appended at the end."""
    report = Report()
    a = ReportItem(type=ItemType.HEADING, content="A", id="aaa")
    b = ReportItem(type=ItemType.PARAGRAPH, content="B", id="bbb")
    report.items = [a, b]

    report.reorder(["bbb"])
    assert [it.id for it in report.items] == ["bbb", "aaa"]


def test_report_update_item():
    report = Report()
    item = ReportItem(type=ItemType.PARAGRAPH, content="old", id="x")
    report.items = [item]
    report.update_item("x", "new")
    assert report.items[0].content == "new"


def test_report_roundtrip():
    report = Report(title="Test Report")
    report.append(ReportItem(type=ItemType.HEADING, content="Title"))
    report.append(ReportItem(type=ItemType.IMAGE, content="data:image/png;base64,x"))

    d = report.to_dict()
    restored = Report.from_dict(d)
    assert restored.title == "Test Report"
    assert len(restored.items) == 2
    assert restored.items[0].type == ItemType.HEADING
    assert restored.items[1].type == ItemType.IMAGE


# --- Additional tests ---


class TestItemType:
    """ItemType enum values and behaviour."""

    def test_enum_values(self):
        assert ItemType.IMAGE.value == "image"
        assert ItemType.HEADING.value == "heading"
        assert ItemType.PARAGRAPH.value == "paragraph"
        assert ItemType.CAPTION.value == "caption"
        assert ItemType.PAGE_BREAK.value == "page_break"

    def test_enum_is_str(self):
        """ItemType inherits from str, so members can be compared to strings."""
        assert ItemType.IMAGE == "image"
        assert ItemType.PAGE_BREAK == "page_break"

    def test_enum_from_value(self):
        assert ItemType("image") is ItemType.IMAGE
        assert ItemType("page_break") is ItemType.PAGE_BREAK

    def test_enum_invalid_value(self):
        import pytest

        with pytest.raises(ValueError):
            ItemType("nonexistent")

    def test_all_members_count(self):
        assert len(ItemType) == 5


class TestReportItemMeta:
    """ReportItem meta field behaviour."""

    def test_default_meta_is_empty_dict(self):
        item = ReportItem(type=ItemType.HEADING, content="H")
        assert item.meta == {}

    def test_meta_roundtrip(self):
        item = ReportItem(
            type=ItemType.HEADING,
            content="H",
            meta={"heading_level": 3, "source_element_id": "chart-1"},
        )
        d = item.to_dict()
        restored = ReportItem.from_dict(d)
        assert restored.meta == {"heading_level": 3, "source_element_id": "chart-1"}

    def test_meta_not_shared_between_instances(self):
        """Default factory must create a new dict for each instance."""
        a = ReportItem(type=ItemType.HEADING, content="A")
        b = ReportItem(type=ItemType.HEADING, content="B")
        a.meta["key"] = "val"
        assert "key" not in b.meta


class TestReportItemId:
    """Auto-generated ID behaviour."""

    def test_auto_id_is_12_hex(self):
        item = ReportItem(type=ItemType.HEADING, content="H")
        assert len(item.id) == 12
        int(item.id, 16)  # should not raise

    def test_explicit_id(self):
        item = ReportItem(type=ItemType.HEADING, content="H", id="my-custom-id")
        assert item.id == "my-custom-id"

    def test_unique_ids(self):
        ids = {ReportItem(type=ItemType.HEADING, content="H").id for _ in range(100)}
        assert len(ids) == 100


class TestReportItemContent:
    """Edge cases for content."""

    def test_default_content_empty_string(self):
        item = ReportItem(type=ItemType.PAGE_BREAK)
        assert item.content == ""

    def test_content_with_unicode(self):
        item = ReportItem(type=ItemType.PARAGRAPH, content="Hello\u2014world \u00e9\u00e8\u00ea")
        d = item.to_dict()
        restored = ReportItem.from_dict(d)
        assert restored.content == "Hello\u2014world \u00e9\u00e8\u00ea"


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

    def test_item_missing_content_defaults_empty(self):
        data = {
            "title": "T",
            "items": [{"id": "abc", "type": "heading"}],
        }
        report = Report.from_dict(data)
        assert report.items[0].content == ""

    def test_item_missing_meta_defaults_empty_dict(self):
        data = {
            "title": "T",
            "items": [{"id": "abc", "type": "paragraph", "content": "text"}],
        }
        report = Report.from_dict(data)
        assert report.items[0].meta == {}

    def test_full_roundtrip_preserves_all_types(self):
        """Every ItemType survives a to_dict/from_dict cycle."""
        report = Report(title="All Types")
        for it_type in ItemType:
            report.append(ReportItem(type=it_type, content=f"content-{it_type.value}"))

        restored = Report.from_dict(report.to_dict())
        assert len(restored.items) == len(ItemType)
        for orig, rest in zip(report.items, restored.items):
            assert orig.type == rest.type
            assert orig.content == rest.content


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
        a = ReportItem(type=ItemType.HEADING, content="A", id="aaa")
        b = ReportItem(type=ItemType.PARAGRAPH, content="B", id="bbb")
        report.items = [a, b]

        # "aaa" appears twice; the dict lookup means only one copy is produced
        report.reorder(["aaa", "aaa", "bbb"])
        ids = [it.id for it in report.items]
        # Should contain each item exactly once
        assert ids.count("aaa") == 1
        assert ids.count("bbb") == 1
        assert ids[0] == "aaa"

    def test_reorder_empty_list(self):
        """Empty reorder list: all items are appended as 'not in list'."""
        report = Report()
        a = ReportItem(type=ItemType.HEADING, content="A", id="aaa")
        b = ReportItem(type=ItemType.PARAGRAPH, content="B", id="bbb")
        report.items = [a, b]
        report.reorder([])
        assert [it.id for it in report.items] == ["aaa", "bbb"]

    def test_reorder_unknown_ids_ignored(self):
        """IDs in the reorder list that don't exist are silently skipped."""
        report = Report()
        a = ReportItem(type=ItemType.HEADING, content="A", id="aaa")
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
        item = ReportItem(type=ItemType.PARAGRAPH, content="original", id="x")
        report.items = [item]
        report.update_item("nonexistent", "new text")
        assert report.items[0].content == "original"

    def test_update_empty_report(self):
        report = Report()
        report.update_item("any", "text")
        assert report.items == []

    def test_remove_nonexistent_id_is_noop(self):
        report = Report()
        item = ReportItem(type=ItemType.HEADING, content="H", id="x")
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
        item = ReportItem(type=ItemType.HEADING, content="H", id="x")
        report.items = [item]
        report.remove("x")
        report.remove("x")
        assert report.items == []


class TestReportAppendMultiple:
    """Append multiple items and verify ordering."""

    def test_append_preserves_order(self):
        report = Report()
        for i in range(5):
            report.append(ReportItem(type=ItemType.PARAGRAPH, content=str(i), id=f"id{i}"))
        assert [it.id for it in report.items] == [f"id{i}" for i in range(5)]

    def test_to_dict_preserves_item_order(self):
        report = Report()
        report.append(ReportItem(type=ItemType.HEADING, content="first", id="a"))
        report.append(ReportItem(type=ItemType.PARAGRAPH, content="second", id="b"))
        d = report.to_dict()
        assert d["items"][0]["id"] == "a"
        assert d["items"][1]["id"] == "b"
