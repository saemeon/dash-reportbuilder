# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Concrete :class:`~dash_reportbuilder.protocols.ReportElement` implementations.

These cover the common cases (heading, paragraph, image, caption, page break).
Custom elements live in user code and just need to implement ``render_into``.

Each element supports JSON round-trip via :meth:`to_dict` / :meth:`from_dict`
so it can be persisted by :class:`~dash_reportbuilder.store.FileStore`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, ClassVar

from dash_reportbuilder.protocols import ReportBackend, ReportElement


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class HeadingElement:
    """A heading."""

    text: str
    level: int = 1
    id: str = field(default_factory=_new_id)

    type: ClassVar[str] = "heading"

    def render_into(self, backend: ReportBackend) -> None:
        backend.add_heading(self.text, self.level)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "level": self.level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HeadingElement:
        return cls(id=data["id"], text=data["text"], level=data.get("level", 1))


@dataclass
class ParagraphElement:
    """A body paragraph."""

    text: str
    id: str = field(default_factory=_new_id)

    type: ClassVar[str] = "paragraph"

    def render_into(self, backend: ReportBackend) -> None:
        backend.add_paragraph(self.text)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.type, "text": self.text}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParagraphElement:
        return cls(id=data["id"], text=data["text"])


@dataclass
class ImageElement:
    """An image (base64 data-URI) with optional title and caption."""

    data_uri: str
    title: str | None = None
    caption: str | None = None
    width_mm: float | None = None
    id: str = field(default_factory=_new_id)

    type: ClassVar[str] = "image"

    def render_into(self, backend: ReportBackend) -> None:
        backend.add_image(
            self.data_uri,
            title=self.title,
            caption=self.caption,
            width_mm=self.width_mm,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "data_uri": self.data_uri,
            "title": self.title,
            "caption": self.caption,
            "width_mm": self.width_mm,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImageElement:
        return cls(
            id=data["id"],
            data_uri=data["data_uri"],
            title=data.get("title"),
            caption=data.get("caption"),
            width_mm=data.get("width_mm"),
        )


@dataclass
class CaptionElement:
    """A standalone caption (centered, italic where supported)."""

    text: str
    id: str = field(default_factory=_new_id)

    type: ClassVar[str] = "caption"

    def render_into(self, backend: ReportBackend) -> None:
        backend.add_caption(self.text)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.type, "text": self.text}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CaptionElement:
        return cls(id=data["id"], text=data["text"])


@dataclass
class PageBreakElement:
    """A page break (no-op where unsupported)."""

    id: str = field(default_factory=_new_id)

    type: ClassVar[str] = "page_break"

    def render_into(self, backend: ReportBackend) -> None:
        backend.add_page_break()

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.type}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PageBreakElement:
        return cls(id=data["id"])


# ---------------------------------------------------------------------------
# Type registry for deserialization
# ---------------------------------------------------------------------------

_BUILTIN: dict[str, Any] = {
    HeadingElement.type: HeadingElement,
    ParagraphElement.type: ParagraphElement,
    ImageElement.type: ImageElement,
    CaptionElement.type: CaptionElement,
    PageBreakElement.type: PageBreakElement,
}


def element_from_dict(data: dict[str, Any]) -> ReportElement:
    """Reconstruct an element from its serialized form.

    The ``type`` field is the discriminator.
    """
    type_name = data.get("type")
    if type_name not in _BUILTIN:
        raise ValueError(f"Unknown element type: {type_name!r}")
    return _BUILTIN[type_name].from_dict(data)


def register_element_type(cls: type) -> type:
    """Register a custom element class for deserialization.

    The class must have a ``type`` class variable and a ``from_dict``
    classmethod.  Useful as a decorator on user-defined elements.
    """
    type_name = getattr(cls, "type", None)
    if not isinstance(type_name, str):
        raise TypeError(f"{cls.__name__} must have a string 'type' class variable")
    _BUILTIN[type_name] = cls
    return cls
