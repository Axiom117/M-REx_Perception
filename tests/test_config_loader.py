"""Generic config loading mechanics (config/loader.py). M1+."""

from __future__ import annotations

from pathlib import Path

import pytest

from mrex_perception.config.loader import config_root, load_config_mapping, require_fields


def test_config_root_points_at_repo_config_dir() -> None:
    root = config_root()
    assert root.is_dir()
    assert (root / "workspace" / "default.yaml").is_file()


def test_load_config_mapping_reads_yaml(tmp_path: Path) -> None:
    (tmp_path / "sample.yaml").write_text("a: 1\nb: [2, 3]\n", encoding="utf-8")
    assert load_config_mapping("sample", tmp_path, label="Test config") == {"a": 1, "b": [2, 3]}


def test_load_config_mapping_treats_name_literally(tmp_path: Path) -> None:
    # config_name is the bare object name; extensions are handled internally.
    (tmp_path / "sample.yml").write_text("a: 1\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="Test config file not found"):
        load_config_mapping("sample.yml", tmp_path, label="Test config")


def test_load_config_mapping_empty_file_gives_empty_dict(tmp_path: Path) -> None:
    (tmp_path / "empty.yaml").write_text("", encoding="utf-8")
    assert load_config_mapping("empty", tmp_path, label="Test config") == {}


def test_load_config_mapping_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Test config file not found"):
        load_config_mapping("nope", tmp_path, label="Test config")


def test_load_config_mapping_rejects_non_mapping(tmp_path: Path) -> None:
    (tmp_path / "list.yaml").write_text("- 1\n- 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="is not a mapping"):
        load_config_mapping("list", tmp_path, label="Test config")


def test_require_fields() -> None:
    require_fields({"a": 1, "b": 2}, ("a", "b"), label="Test config")
    with pytest.raises(ValueError, match="missing fields: b"):
        require_fields({"a": 1}, ("a", "b"), label="Test config")
