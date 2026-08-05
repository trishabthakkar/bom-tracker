import pytest

from app.services.file_storage import BACKEND_ROOT, get_upload_directory, resolve_storage_path


def test_upload_directory_defaults_to_backend_uploads() -> None:
    assert get_upload_directory() == BACKEND_ROOT / "uploads"


def test_resolve_storage_path_finds_backend_upload_for_legacy_relative_path(
    tmp_path,
) -> None:
    stored_file = get_upload_directory() / "resolver-test.csv"
    stored_file.parent.mkdir(parents=True, exist_ok=True)
    stored_file.write_text("Part Number\nPN-1\n", encoding="utf-8")

    try:
        assert resolve_storage_path("uploads/resolver-test.csv") == stored_file
    finally:
        stored_file.unlink(missing_ok=True)


def test_resolve_storage_path_returns_absolute_paths_unchanged(tmp_path) -> None:
    absolute_path = tmp_path / "somewhere-else.csv"

    assert resolve_storage_path(absolute_path) == absolute_path


def test_resolve_storage_path_rejects_relative_paths_outside_upload_directory() -> None:
    with pytest.raises(FileNotFoundError):
        resolve_storage_path("../../etc/passwd")
