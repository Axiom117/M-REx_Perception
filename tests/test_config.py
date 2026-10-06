"""Config layer tests: loader mechanics + workspace YAML loading/validation (M1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from mrex_perception.config.app import AppConfig, load_app_config
from mrex_perception.config.loader import config_root, load_config_mapping, require_fields
from mrex_perception.config.workspace import list_workspace_configs, load_workspace

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config" / "workspace"


def test_config_root_and_mapping(tmp_path: Path) -> None:
    root = config_root()
    assert (root / "workspace" / "default.yaml").is_file()

    (tmp_path / "sample.yaml").write_text("a: 1\nb: [2, 3]\n", encoding="utf-8")
    assert load_config_mapping("sample", tmp_path, label="Test config") == {"a": 1, "b": [2, 3]}

    # config_name is the bare object name; extensions are handled internally
    (tmp_path / "sample.yml").write_text("a: 1\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="Test config file not found"):
        load_config_mapping("sample.yml", tmp_path, label="Test config")

    (tmp_path / "empty.yaml").write_text("", encoding="utf-8")
    assert load_config_mapping("empty", tmp_path, label="Test config") == {}


def test_loader_errors(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Test config file not found"):
        load_config_mapping("nope", tmp_path, label="Test config")

    (tmp_path / "list.yaml").write_text("- 1\n- 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="is not a mapping"):
        load_config_mapping("list", tmp_path, label="Test config")

    require_fields({"a": 1, "b": 2}, ("a", "b"), label="Test config")
    with pytest.raises(ValueError, match="missing fields: b"):
        require_fields({"a": 1}, ("a", "b"), label="Test config")


def test_load_default_workspace() -> None:
    ws = load_workspace("default")
    assert list(ws.size) == [100.0, 40.0, 10.0]
    assert list(ws.source_region) == [0.0, 5.0, 30.0, 30.0]
    assert list(ws.moved_region) == [40.0, 5.0, 45.0, 30.0]
    assert ws.moved_spacing == 4.0
    assert ws.material == "glass"
    assert ws.surface_height == 0.0
    assert ws.coeff_friction == 0.4
    assert ws.youngs_modulus == 7e10
    assert ws.poisson_ratio == 0.22
    assert ws.density == 2500.0
    assert ws.surface_energy == 0.1


def test_workspace_errors_and_extension(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        load_workspace("does_not_exist", config_dir=tmp_path)

    # missing required fields are reported natively by pydantic
    (tmp_path / "broken.yaml").write_text("size: [100, 40, 10]\n", encoding="utf-8")
    with pytest.raises(ValueError) as excinfo:
        load_workspace("broken", config_dir=tmp_path)
    assert "Field required" in str(excinfo.value)
    assert "source_region" in str(excinfo.value)

    text = (CONFIG_DIR / "default.yaml").read_text(encoding="utf-8")
    bad = text.replace("source_region: [0, 5, 30, 30]", "source_region: [0, 5, 30]")
    (tmp_path / "bad.yaml").write_text(bad, encoding="utf-8")
    with pytest.raises(ValueError, match="3, 4, and 4 values"):
        load_workspace("bad", config_dir=tmp_path)

    (tmp_path / "alt.yml").write_text(text, encoding="utf-8")
    assert load_workspace("alt", config_dir=tmp_path).material == "glass"


def test_list_workspace_configs(tmp_path: Path) -> None:
    # the repo config dir always contains default.yaml
    assert "default" in list_workspace_configs()

    # stems are sorted and de-duplicated across .yaml/.yml; missing dir -> []
    (tmp_path / "b.yaml").write_text("", encoding="utf-8")
    (tmp_path / "a.yml").write_text("", encoding="utf-8")
    (tmp_path / "b.yml").write_text("", encoding="utf-8")
    assert list_workspace_configs(tmp_path) == ["a", "b"]
    assert list_workspace_configs(tmp_path / "missing") == []


def test_load_app_config(tmp_path: Path) -> None:
    config = load_app_config()
    assert isinstance(config, AppConfig)
    assert config.workspace.material == "glass"

    text = (CONFIG_DIR / "default.yaml").read_text(encoding="utf-8")
    alt_text = text.replace("material: glass", "material: quartz")
    (tmp_path / "alt.yaml").write_text(alt_text, encoding="utf-8")
    assert load_app_config("alt", config_dir=tmp_path).workspace.material == "quartz"
