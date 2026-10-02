"""Workspace YAML loading and validation (M1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from mrex_perception.config.workspace import load_workspace

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config" / "workspace"


def test_load_default_workspace() -> None:
    ws = load_workspace("default")
    assert list(ws.size) == [100.0, 40.0, 10.0]
    assert list(ws.source_region) == [0.0, 5.0, 20.0, 25.0]
    assert list(ws.moved_region) == [80.0, 5.0, 100.0, 25.0]
    assert ws.moved_spacing == 4.0
    assert ws.material == "glass"
    assert ws.surface_height == 0.0
    assert ws.coeff_friction == 0.4
    assert ws.youngs_modulus == 7e10
    assert ws.poisson_ratio == 0.22
    assert ws.density == 2500.0
    assert ws.surface_energy == 0.1


def test_missing_file_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        load_workspace("does_not_exist", config_dir=tmp_path)


def test_missing_fields_error(tmp_path: Path) -> None:
    (tmp_path / "broken.yaml").write_text("size: [100, 40, 10]\n", encoding="utf-8")
    with pytest.raises(ValueError) as excinfo:
        load_workspace("broken", config_dir=tmp_path)
    message = str(excinfo.value)
    assert "missing fields" in message
    assert "density" in message


def test_wrong_vector_length_error(tmp_path: Path) -> None:
    text = (CONFIG_DIR / "default.yaml").read_text(encoding="utf-8")
    bad = text.replace("sourceregion: [0, 5, 20, 25]", "sourceregion: [0, 5, 20]")
    (tmp_path / "bad.yaml").write_text(bad, encoding="utf-8")
    with pytest.raises(ValueError, match="3, 4, and 4 values"):
        load_workspace("bad", config_dir=tmp_path)


def test_yml_extension_supported(tmp_path: Path) -> None:
    text = (CONFIG_DIR / "default.yaml").read_text(encoding="utf-8")
    (tmp_path / "alt.yml").write_text(text, encoding="utf-8")
    assert load_workspace("alt", config_dir=tmp_path).material == "glass"
