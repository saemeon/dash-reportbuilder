# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Data model for report items and reports."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ItemType(str, Enum):
    """Type of report item."""

    IMAGE = "image"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    CAPTION = "caption"
    PAGE_BREAK = "page_break"


@dataclass
class ReportItem:
    """A single item in a report.

    Parameters
    ----------
    type : ItemType
        The kind of item.
    content : str
        For images: base64 data-URI.  For text types: the text string.
    id : str
        Unique identifier (auto-generated).
    meta : dict
        Optional metadata (e.g. ``heading_level``, ``source_element_id``).
    """

    type: ItemType
    content: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReportItem:
        return cls(
            id=data["id"],
            type=ItemType(data["type"]),
            content=data.get("content", ""),
            meta=data.get("meta", {}),
        )


@dataclass
class Report:
    """An ordered collection of report items.

    Parameters
    ----------
    title : str
        Report title (used in exports).
    items : list[ReportItem]
        The items in display order.
    """

    title: str = "Untitled Report"
    items: list[ReportItem] = field(default_factory=list)

    def append(self, item: ReportItem) -> None:
        """Add an item to the end of the report."""
        self.items.append(item)

    def remove(self, item_id: str) -> None:
        """Remove an item by ID."""
        self.items = [it for it in self.items if it.id != item_id]

    def reorder(self, item_ids: list[str]) -> None:
        """Reorder items to match *item_ids* sequence."""
        by_id = {it.id: it for it in self.items}
        seen: set[str] = set()
        reordered: list[ReportItem] = []
        for iid in item_ids:
            if iid in by_id and iid not in seen:
                reordered.append(by_id[iid])
                seen.add(iid)
        # Append any items not in the list (safety net)
        for it in self.items:
            if it.id not in seen:
                reordered.append(it)
        self.items = reordered

    def update_item(self, item_id: str, content: str) -> None:
        """Update the content of an item by ID."""
        for it in self.items:
            if it.id == item_id:
                it.content = content
                return

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "items": [it.to_dict() for it in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Report:
        return cls(
            title=data.get("title", "Untitled Report"),
            items=[ReportItem.from_dict(d) for d in data.get("items", [])],
        )
