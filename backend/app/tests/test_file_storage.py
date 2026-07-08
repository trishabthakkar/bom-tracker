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
