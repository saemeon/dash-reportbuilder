# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Report model — a list of :class:`~dash_reportbuilder.protocols.ReportElement`."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dash_reportbuilder.elements import element_from_dict
from dash_reportbuilder.protocols import ReportBackend, ReportElement

__all__ = ["Report"]


@dataclass
class Report:
    """An ordered collection of report elements.

    The report itself is dumb — it just holds a list.  Each element is
    responsible for knowing how to render itself; each backend is
    responsible for knowing how to produce its format.

    Parameters
    ----------
    title : str
        Report title (used as the top-level heading by some backends).
    items : list[ReportElement]
        The elements in display order.
    """

    title: str = "Untitled Report"
    items: list[Any] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, item: ReportElement) -> None:
        """Append *item* to the end of the report."""
        self.items.append(item)

    # Backwards-compatible alias.
    append = add

    def remove(self, item_id: str) -> None:
        """Remove an element by its ``id`` field."""
        self.items = [it for it in self.items if getattr(it, "id", None) != item_id]

    def reorder(self, item_ids: list[str]) -> None:
        """Reorder elements to match *item_ids*; unknown IDs are ignored."""
        by_id = {getattr(it, "id", None): it for it in self.items}
        seen: set[str] = set()
        reordered: list[ReportElement] = []
        for iid in item_ids:
            if iid in by_id and iid not in seen:
                reordered.append(by_id[iid])
                seen.add(iid)
        reordered.extend(it for it in self.items if getattr(it, "id", None) not in seen)
        self.items = reordered

    def update_item(self, item_id: str, **fields: Any) -> None:
        """Update fields on the element with the given ``id``."""
        for it in self.items:
            if getattr(it, "id", None) == item_id:
                for k, v in fields.items():
                    setattr(it, k, v)
                return

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export(self, backend: ReportBackend) -> bytes:
        """Render every element into *backend* and return the bytes."""
        for item in self.items:
            item.render_into(backend)
        return backend.build()

    # ------------------------------------------------------------------
    # Serialization (for FileStore)
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report to a JSON-safe dict."""
        return {
            "title": self.title,
            "items": [it.to_dict() for it in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Report:
        """Reconstruct a report from a serialized dict."""
        return cls(
            title=data.get("title", "Untitled Report"),
            items=[element_from_dict(d) for d in data.get("items", [])],
        )
