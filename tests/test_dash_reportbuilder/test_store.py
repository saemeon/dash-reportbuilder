# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

import tempfile
import threading
from pathlib import Path

from dash_reportbuilder.elements import (
    HeadingElement,
    ImageElement,
    ParagraphElement,
)
from dash_reportbuilder.model import Report
from dash_reportbuilder.store import FileStore, MemoryStore, ReportStore


def test_memory_store_get_creates_empty():
    store = MemoryStore()
    report = store.get("session1")
    assert report.items == []
    assert report.title == "Untitled Report"


def test_memory_store_put_get():
    store = MemoryStore()
    report = store.get("session1")
    report.append(HeadingElement(text="Hello", level=2))
    store.put("session1", report)

    loaded = store.get("session1")
    assert len(loaded.items) == 1
    assert loaded.items[0].text == "Hello"


def test_memory_store_delete():
    store = MemoryStore()
    report = store.get("s1")
    report.append(HeadingElement(text="X", level=2))
    store.put("s1", report)
    store.delete("s1")
    assert store.get("s1").items == []


def test_memory_store_isolation():
    store = MemoryStore()
    r1 = store.get("s1")
    r1.append(HeadingElement(text="A", level=2))
    store.put("s1", r1)

    r2 = store.get("s2")
    assert r2.items == []


def test_file_store_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileStore(tmpdir)
        report = store.get("session1")
        report.append(ImageElement(data_uri="data:image/png;base64,abc"))
        report.title = "My Report"
        store.put("session1", report)

        loaded = store.get("session1")
        assert len(loaded.items) == 1
        assert loaded.items[0].data_uri == "data:image/png;base64,abc"
        assert loaded.title == "My Report"


def test_file_store_delete():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileStore(tmpdir)
        report = store.get("s1")
        report.append(HeadingElement(text="X", level=2))
        store.put("s1", report)

        store.delete("s1")
        assert not (Path(tmpdir) / "s1.json").exists()
        assert store.get("s1").items == []


def test_file_store_default_directory():
    store = FileStore()
    assert store._dir.exists()


# --- Additional tests ---


class TestReportStoreProtocol:
    """Both stores satisfy the ReportStore protocol."""

    def test_memory_store_is_report_store(self):
        assert isinstance(MemoryStore(), ReportStore)

    def test_file_store_is_report_store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert isinstance(FileStore(tmpdir), ReportStore)


class TestFileStorePathSanitization:
    """FileStore prevents path traversal via session_id."""

    def test_dotdot_sanitized(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileStore(tmpdir)
            path = store._path("../../etc/passwd")
            assert str(path).startswith(str(store._dir))
            assert ".." not in path.name

    def test_slash_sanitized(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileStore(tmpdir)
            path = store._path("foo/bar/baz")
            assert "/" not in path.name.replace(".json", "")

    def test_traversal_does_not_escape_directory(self):
        """Putting with a traversal session_id writes inside the store dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileStore(tmpdir)
            report = Report(title="evil")
            store.put("../../../tmp/evil", report)
            written_files = list(Path(tmpdir).glob("*.json"))
            assert len(written_files) == 1
            assert written_files[0].parent == Path(tmpdir)

    def test_get_after_sanitized_put(self):
        """Get with the same traversal ID finds the sanitized file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileStore(tmpdir)
            report = Report(title="safe")
            report.append(HeadingElement(text="H", level=2))
            store.put("../bad", report)
            loaded = store.get("../bad")
            assert loaded.title == "safe"
            assert len(loaded.items) == 1


class TestMemoryStoreThreadSafety:
    """Concurrent puts should not corrupt state."""

    def test_concurrent_puts(self):
        store = MemoryStore()
        errors = []

        def writer(session: str, n: int):
            try:
                for i in range(n):
                    report = Report(title=f"{session}-{i}")
                    report.append(ParagraphElement(text=f"item-{i}"))
                    store.put(session, report)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=writer, args=(f"session-{t}", 50))
            for t in range(10)
        ]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        assert errors == []
        for t in range(10):
            r = store.get(f"session-{t}")
            assert len(r.items) == 1

    def test_concurrent_get_and_put(self):
        store = MemoryStore()
        store.put("shared", Report(title="initial"))
        errors = []

        def reader():
            try:
                for _ in range(100):
                    r = store.get("shared")
                    assert isinstance(r, Report)
            except Exception as exc:
                errors.append(exc)

        def writer():
            try:
                for i in range(100):
                    r = Report(title=f"v{i}")
                    store.put("shared", r)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=reader) for _ in range(5)]
        threads.append(threading.Thread(target=writer))
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        assert errors == []


class TestFileStoreMultipleSessions:
    """FileStore with multiple sessions side by side."""

    def test_multiple_sessions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileStore(tmpdir)
            for sid in ["alpha", "beta", "gamma"]:
                r = Report(title=sid)
                r.append(HeadingElement(text=f"Title for {sid}", level=2))
                store.put(sid, r)

            for sid in ["alpha", "beta", "gamma"]:
                loaded = store.get(sid)
                assert loaded.title == sid
                assert loaded.items[0].text == f"Title for {sid}"

    def test_delete_one_session_keeps_others(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileStore(tmpdir)
            for sid in ["a", "b", "c"]:
                store.put(sid, Report(title=sid))

            store.delete("b")
            assert store.get("a").title == "a"
            assert store.get("b").title == "Untitled Report"
            assert store.get("c").title == "c"

    def test_file_count_matches_sessions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileStore(tmpdir)
            for sid in ["x", "y", "z"]:
                store.put(sid, Report(title=sid))
            json_files = list(Path(tmpdir).glob("*.json"))
            assert len(json_files) == 3


class TestPutOverwrites:
    """put overwrites existing report, in both stores."""

    def test_memory_store_put_overwrites(self):
        store = MemoryStore()
        r1 = Report(title="first")
        r1.append(HeadingElement(text="H1", level=2))
        store.put("s", r1)

        r2 = Report(title="second")
        r2.append(ParagraphElement(text="P"))
        r2.append(ParagraphElement(text="Q"))
        store.put("s", r2)

        loaded = store.get("s")
        assert loaded.title == "second"
        assert len(loaded.items) == 2

    def test_file_store_put_overwrites(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileStore(tmpdir)
            r1 = Report(title="v1")
            r1.append(HeadingElement(text="old", level=2))
            store.put("s", r1)

            r2 = Report(title="v2")
            store.put("s", r2)

            loaded = store.get("s")
            assert loaded.title == "v2"
            assert loaded.items == []


class TestDeleteNonexistent:
    """Deleting a session that doesn't exist should not error."""

    def test_memory_store_delete_nonexistent(self):
        store = MemoryStore()
        store.delete("does-not-exist")

    def test_file_store_delete_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileStore(tmpdir)
            store.delete("does-not-exist")
