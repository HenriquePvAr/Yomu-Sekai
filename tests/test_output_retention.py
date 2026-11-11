import sqlite3
import uuid
from pathlib import Path

import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from yomu.runtime.output_retention import prune_chapter_runs


def _run(chapter: Path, age: int) -> Path:
    folder = chapter / str(uuid.uuid4())
    folder.mkdir(parents=True)
    (folder / "artifact.bin").write_bytes(b"data")
    folder.touch()
    import os
    os.utime(folder, (1_700_000_000 - age, 1_700_000_000 - age))
    return folder


def _published_db(path: Path, run_id: str):
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE community_posts (source_run_id TEXT, output_dir TEXT, "
        "status TEXT, deleted_at REAL)"
    )
    connection.execute(
        "INSERT INTO community_posts VALUES (?, ?, 'published', NULL)",
        (run_id, ""),
    )
    connection.commit()
    connection.close()


def test_prunes_old_runs_but_keeps_newest_protected_active_and_published(tmp_path):
    chapter = tmp_path / "chapter"
    chapter.mkdir()
    newest = _run(chapter, 1)
    second = _run(chapter, 2)
    protected = _run(chapter, 3)
    interrupted = _run(chapter, 4)
    published = _run(chapter, 5)
    ordinary_old = _run(chapter, 6)
    jobs = [{"run_id": interrupted.name, "status": "interrupted"}]
    community = tmp_path / "community.sqlite3"
    _published_db(community, published.name)
    removed, hidden = [], []

    def delete_tree(path):
        import shutil
        shutil.rmtree(path)
        removed.append(path.name)
        return True, "removed"

    result = prune_chapter_runs(
        chapter, 2, {protected.name}, jobs=jobs,
        community_db_path=community, delete_tree=delete_tree,
        hide_record=lambda record: hidden.append(record["output_folder"]),
    )

    assert result["removed"] == [ordinary_old.name]
    assert removed == [ordinary_old.name]
    assert hidden == [str(ordinary_old)]
    assert all(path.exists() for path in (newest, second, protected, interrupted, published))
    assert not ordinary_old.exists()


def test_keep_zero_never_calls_deletion_and_delete_failure_is_reported(tmp_path):
    chapter = tmp_path / "chapter"
    chapter.mkdir()
    older = _run(chapter, 2)
    _run(chapter, 1)
    called = []
    noop = lambda path: called.append(path)
    assert prune_chapter_runs(chapter, 0, delete_tree=noop, hide_record=lambda record: None)["disabled"]
    assert called == []

    def deny_delete(_path):
        raise PermissionError("locked")

    result = prune_chapter_runs(
        chapter, 1, delete_tree=deny_delete, hide_record=lambda record: None,
    )
    assert result["removed"] == []
    assert any(item["run_id"] == older.name and item["reason"] ==
               "delete_failed:PermissionError" for item in result["preserved"])
