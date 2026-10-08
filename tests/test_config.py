"""Config layer tests: loader mechanics + workspace YAML loading/validation (M1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from mrex_perception.config.app import AppConfig, load_app_config
from mrex_perception.config.embryo import list_embryo_configs, load_embryo
from mrex_perception.config.loader import config_root, load_config_mapping, require_fields
from mrex_perception.config.tool_head import list_tool_head_configs, load_tool_head
from mrex_perception.config.workspace import list_workspace_configs, load_workspace

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config" / "workspace"


def test_config_root_and_mapping(tmp_path: Path) -> None:
    root = config_root()
    assert (root / "workspace" / "default.yaml").is_file()

    (tmp_path / "sample.yaml").write_text("a: 1\nb: [2, 3]\n", encoding="utf-8")
    assert load_config_mapping("sample", tmp_path, label="Test config") == {"a": 1, "b": [2, 3]}

    # only the .yaml extension is resolved: a same-named .yml file is not picked up...
    (tmp_path / "legacy.yml").write_text("a: 1\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="Test config file not found"):
        load_config_mapping("legacy", tmp_path, label="Test config")

    # ...and config_name is the bare name (passing an extension never matches)
    with pytest.raises(FileNotFoundError, match="Test config file not found"):
        load_config_mapping("sample.yaml", tmp_path, label="Test config")

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

    (tmp_path / "alt.yaml").write_text(text, encoding="utf-8")
    assert load_workspace("alt", config_dir=tmp_path).material == "glass"

    # .yml is not supported: a same-named .yml file is ignored
    (tmp_path / "legacy.yml").write_text(text, encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="not found"):
        load_workspace("legacy", config_dir=tmp_path)


def test_list_workspace_configs(tmp_path: Path) -> None:
    # the repo config dir always contains default.yaml
    assert "default" in list_workspace_configs()

    # only *.yaml is listed (sorted); a .yml file is ignored; missing dir -> []
    (tmp_path / "b.yaml").write_text("", encoding="utf-8")
    (tmp_path / "a.yaml").write_text("", encoding="utf-8")
    (tmp_path / "c.yml").write_text("", encoding="utf-8")
    assert list_workspace_configs(tmp_path) == ["a", "b"]
    assert list_workspace_configs(tmp_path / "missing") == []


def test_load_app_config(tmp_path: Path) -> None:
    config = load_app_config()
    assert isinstance(config, AppConfig)
    assert config.workspace.material == "glass"
    assert config.embryo.width == pytest.approx(0.2)
    assert config.tool.adhesion.base_probability == pytest.approx(0.7)

    # config_dir overrides the config root (workspace/ + embryo/ + tool_head/)
    _copy_default_configs(tmp_path)
    _write_alt(
        tmp_path / "workspace" / "default.yaml",
        tmp_path / "workspace" / "alt.yaml",
        "material: glass",
        "material: quartz",
    )
    _write_alt(
        tmp_path / "embryo" / "default.yaml",
        tmp_path / "embryo" / "alt.yaml",
        "width: 0.2",
        "width: 0.3",
    )
    _write_alt(
        tmp_path / "tool_head" / "default.yaml",
        tmp_path / "tool_head" / "alt.yaml",
        "base_probability: 0.7",
        "base_probability: 0.9",
    )

    alt = load_app_config("alt", "alt", "alt", config_dir=tmp_path)
    assert alt.workspace.material == "quartz"
    assert alt.embryo.width == pytest.approx(0.3)
    assert alt.tool.adhesion.base_probability == pytest.approx(0.9)


def test_load_default_embryo() -> None:
    spec = load_embryo("default")
    assert spec.shape == "ellipsoid"
    assert spec.width == pytest.approx(0.2)
    assert spec.length == pytest.approx(0.5)
    assert spec.height == pytest.approx(0.2)
    assert spec.min_confidence == pytest.approx(0.8)
    assert spec.cluster_threshold == pytest.approx(1.0)
    assert spec.min_spacing == pytest.approx(1.0)


def test_load_default_tool_head() -> None:
    config = load_tool_head("default")
    assert config.name == "adhesionTool"
    assert config.shape == "cylinder"
    assert config.diameter == pytest.approx(1.5)
    assert config.height == pytest.approx(0.5)
    assert config.contact_surface.shape == "circular"
    assert config.contact_surface.radius == pytest.approx(0.25)
    assert config.adhesion.model == "vanDerWaalsDroplet"
    assert config.adhesion.base_probability == pytest.approx(0.7)
    assert config.adhesion.reference_width == pytest.approx(0.2)
    assert config.adhesion.attempt_penalty == pytest.approx(0.05)
    assert config.adhesion.max_attempts == 3
    assert config.clearance == pytest.approx(1.0)
    assert config.max_velocity == pytest.approx(10.0)
    assert config.home_offset == [15.0, 15.0, 10.0]

    # full mapping onto the core model (catches a forgotten assignment)
    tool = config.to_tool_head(load_workspace("default"))
    assert tool.name == "adhesionTool"
    assert tool.shape == "cylinder"
    assert tool.diameter == pytest.approx(1.5)
    assert tool.height == pytest.approx(0.5)
    assert tool.contact_shape == "circular"
    assert tool.contact_radius == pytest.approx(0.25)
    assert tool.clearance == pytest.approx(1.0)
    assert tool.max_velocity == pytest.approx(10.0)
    assert tool.adhesion_model == "vanDerWaalsDroplet"
    assert tool.base_probability == pytest.approx(0.7)
    assert tool.reference_width == pytest.approx(0.2)
    assert tool.attempt_penalty == pytest.approx(0.05)
    assert tool.max_attempts == 3
    # home position from home_offset: source region [0, 5, ...] -> [15, 17.5, 10]
    assert tool.position == pytest.approx([15.0, 17.5, 10.0])
    assert tool.home_position == pytest.approx([15.0, 17.5, 10.0])


def test_tool_head_config_errors(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Tool head config file not found"):
        load_tool_head("nope", config_dir=tmp_path)

    text = (config_root() / "tool_head" / "default.yaml").read_text(encoding="utf-8")
    (tmp_path / "bad.yaml").write_text(
        text.replace("home_offset: [15, 15, 10]", "home_offset: [15, 10]"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="home_offset must contain 3 values"):
        load_tool_head("bad", config_dir=tmp_path)

    (tmp_path / "broken.yaml").write_text("name: adhesionTool\n", encoding="utf-8")
    with pytest.raises(ValueError) as excinfo:
        load_tool_head("broken", config_dir=tmp_path)
    assert "Field required" in str(excinfo.value)
    assert "adhesion" in str(excinfo.value)


def test_embryo_config_errors(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Embryo config file not found"):
        load_embryo("nope", config_dir=tmp_path)

    (tmp_path / "broken.yaml").write_text("shape: ellipsoid\n", encoding="utf-8")
    with pytest.raises(ValueError) as excinfo:
        load_embryo("broken", config_dir=tmp_path)
    assert "Field required" in str(excinfo.value)
    assert "width" in str(excinfo.value)


def test_list_embryo_and_tool_head_configs(tmp_path: Path) -> None:
    assert "default" in list_embryo_configs()
    assert "default" in list_tool_head_configs()

    (tmp_path / "b.yaml").write_text("", encoding="utf-8")
    (tmp_path / "a.yaml").write_text("", encoding="utf-8")
    (tmp_path / "c.yml").write_text("", encoding="utf-8")
    assert list_embryo_configs(tmp_path) == ["a", "b"]
    assert list_tool_head_configs(tmp_path) == ["a", "b"]


def _copy_default_configs(destination: Path) -> None:
    """Copy the shipped config tree (workspace/ embryo/ tool_head/) into ``destination``."""
    root = config_root()
    for section in ("workspace", "embryo", "tool_head"):
        (destination / section).mkdir(parents=True)
        for path in (root / section).glob("*.yaml"):
            (destination / section / path.name).write_text(
                path.read_text(encoding="utf-8"), encoding="utf-8"
            )


def _write_alt(source: Path, destination: Path, old: str, new: str) -> None:
    """Write a copy of ``source`` with ``old`` replaced by ``new`` (test helper)."""
    destination.write_text(source.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
