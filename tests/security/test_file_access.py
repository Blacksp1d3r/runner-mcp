from pathlib import Path

import pytest

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.file_access import FileAccessError, FileAccessPolicy, FileAccessService


def service_for(root: Path, policy: FileAccessPolicy | None = None) -> FileAccessService:
    root.mkdir(parents=True, exist_ok=True)
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=root,
            )
        }
    )
    return FileAccessService(registry, policy=policy)


def test_read_file_is_paginated_and_never_returns_project_root(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = service_for(root)
    (root / "notes.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")

    result = service.read_file("demo", "notes.txt", offset=1, length=1)

    assert result["path"] == "notes.txt"
    assert result["content"] == "two\n"
    assert result["next_offset"] == 2
    assert result["eof"] is False
    assert str(root) not in repr(result)


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt",
        "/absolute/path.txt",
        "folder\\file.txt",
    ],
)
def test_traversal_absolute_and_backslash_paths_are_rejected(
    tmp_path: Path,
    path: str,
) -> None:
    service = service_for(tmp_path / "project")

    with pytest.raises(FileAccessError):
        service.read_file("demo", path)


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = service_for(root)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    (root / "link.txt").symlink_to(outside)

    with pytest.raises(FileAccessError, match="Symlinks"):
        service.read_file("demo", "link.txt")


def test_secret_paths_are_blocked_and_hidden_from_listing(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = service_for(root)
    (root / ".env").write_text("SECRET=value", encoding="utf-8")
    (root / ".env.example").write_text("SECRET=", encoding="utf-8")
    (root / "visible.txt").write_text("ok", encoding="utf-8")

    with pytest.raises(FileAccessError, match="blocked"):
        service.read_file("demo", ".env")

    listing = service.list_files("demo")
    names = {entry["name"] for entry in listing["entries"]}
    assert ".env" not in names
    assert ".env.example" in names
    assert "visible.txt" in names


def test_private_key_marker_blocks_an_otherwise_allowed_text_file(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = service_for(root)
    (root / "notes.txt").write_text(
        "-----BEGIN PRIVATE KEY-----\nnot-a-real-key\n",
        encoding="utf-8",
    )

    with pytest.raises(FileAccessError, match="secret policy"):
        service.read_file("demo", "notes.txt")


def test_known_secret_assignments_are_redacted(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = service_for(root)
    secret_value = "abcdefghijklmnopqrstuvwx"
    (root / "settings.txt").write_text(
        f"token={secret_value}\nmode=safe\n",
        encoding="utf-8",
    )

    result = service.read_file("demo", "settings.txt")

    assert secret_value not in result["content"]
    assert "token=[REDACTED]" in result["content"]
    assert "mode=safe" in result["content"]


def test_binary_files_are_rejected(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = service_for(root)
    (root / "binary.bin").write_bytes(b"abc\x00def")

    with pytest.raises(FileAccessError, match="Binary"):
        service.read_file("demo", "binary.bin")


def test_file_size_limit_is_enforced(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = service_for(root, FileAccessPolicy(max_file_bytes=8))
    (root / "large.txt").write_text("0123456789", encoding="utf-8")

    with pytest.raises(FileAccessError, match="read-size"):
        service.read_file("demo", "large.txt")


def test_listing_pagination_and_metadata(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = service_for(root)
    for name in ("a.txt", "b.txt", "c.txt"):
        (root / name).write_text(name, encoding="utf-8")

    listing = service.list_files("demo", limit=2)
    assert [entry["name"] for entry in listing["entries"]] == ["a.txt", "b.txt"]
    assert listing["next_offset"] == 2
    assert listing["eof"] is False

    metadata = service.file_metadata("demo", "a.txt")
    assert metadata["path"] == "a.txt"
    assert metadata["type"] == "file"
    assert metadata["within_read_limit"] is True
    assert str(root) not in repr(metadata)


def test_unknown_project_is_rejected_without_path_information(tmp_path: Path) -> None:
    service = service_for(tmp_path / "project")

    with pytest.raises(FileAccessError, match="Unknown or disabled project") as exc:
        service.read_file("missing", "notes.txt")

    assert str(tmp_path) not in str(exc.value)


def test_code_like_token_assignment_is_not_redacted(tmp_path: Path) -> None:
    root = tmp_path / "project"
    service = service_for(root)
    source = 'token = request.headers.get("Authorization")\n'
    (root / "auth.py").write_text(source, encoding="utf-8")

    result = service.read_file("demo", "auth.py")

    assert result["content"] == source
