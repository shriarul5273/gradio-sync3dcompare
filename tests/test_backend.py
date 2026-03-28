"""
Backend tests for Sync3DCompare component.
Tests validation logic, postprocessing, and error cases.
"""
import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from gradio_sync3dcompare import Sync3DCompare


def make_component(**kwargs):
    """Create a Sync3DCompare instance, bypassing Gradio Component __init__ side effects."""
    comp = object.__new__(Sync3DCompare)
    comp.render_mode = kwargs.get("render_mode", "points")
    comp.sync_camera = kwargs.get("sync_camera", True)
    comp.point_size = kwargs.get("point_size", 2.0)
    comp.max_point_size = kwargs.get("max_point_size", 10.0)
    comp.height = kwargs.get("height", 500)
    comp.default_zoom = kwargs.get("default_zoom", 1.0)
    comp.min_zoom = kwargs.get("min_zoom", 0.5)
    comp.max_zoom = kwargs.get("max_zoom", 16.0)
    comp.max_views = kwargs.get("max_views", 4)
    return comp


class TestValidation:

    def test_valid_minimal_ply(self):
        comp = make_component()
        result = comp._validate_assets([{"path": "a.ply", "type": "ply"}])
        assert len(result) == 1
        assert result[0]["path"] == "a.ply"
        assert result[0]["type"] == "ply"
        assert result[0]["visible"] is True
        assert result[0]["name"] == "Asset 1"

    def test_valid_minimal_glb(self):
        comp = make_component()
        result = comp._validate_assets([{"path": "a.glb", "type": "glb"}])
        assert result[0]["type"] == "glb"

    def test_valid_multiple_assets(self):
        comp = make_component()
        assets = [
            {"path": "a.ply", "type": "ply"},
            {"path": "b.glb", "type": "glb"},
            {"path": "c.ply", "type": "ply"},
        ]
        result = comp._validate_assets(assets)
        assert len(result) == 3

    def test_valid_mixed_assets_up_to_max_views(self):
        comp = make_component(max_views=4)
        assets = [
            {"path": "a.ply", "type": "ply"},
            {"path": "b.glb", "type": "glb"},
            {"path": "c.ply", "type": "ply"},
            {"path": "d.glb", "type": "glb"},
        ]
        result = comp._validate_assets(assets)
        assert len(result) == 4

    def test_name_preserved_when_given(self):
        comp = make_component()
        result = comp._validate_assets([{"name": "GT", "path": "gt.ply", "type": "ply"}])
        assert result[0]["name"] == "GT"

    def test_name_defaults_when_missing(self):
        comp = make_component()
        result = comp._validate_assets([
            {"path": "a.ply", "type": "ply"},
            {"path": "b.ply", "type": "ply"},
        ])
        assert result[0]["name"] == "Asset 1"
        assert result[1]["name"] == "Asset 2"

    def test_valid_color(self):
        comp = make_component()
        result = comp._validate_assets([
            {"path": "a.ply", "type": "ply", "color": [255, 128, 0]}
        ])
        assert result[0]["color"] == [255, 128, 0]

    def test_visible_defaults_true(self):
        comp = make_component()
        result = comp._validate_assets([{"path": "a.ply", "type": "ply"}])
        assert result[0]["visible"] is True

    def test_visible_false_preserved(self):
        comp = make_component()
        result = comp._validate_assets([
            {"path": "a.ply", "type": "ply", "visible": False}
        ])
        assert result[0]["visible"] is False

    def test_metadata_preserved(self):
        comp = make_component()
        result = comp._validate_assets([
            {"path": "a.ply", "type": "ply", "metadata": {"source": "test"}}
        ])
        assert result[0]["metadata"] == {"source": "test"}

    def test_type_inferred_from_glb_extension(self):
        comp = make_component()
        result = comp._validate_assets([{"path": "mesh_a.glb"}])
        assert result[0]["type"] == "glb"

    def test_pathlike_input_is_supported(self):
        comp = make_component()
        result = comp._validate_assets([{"path": Path("mesh_a.glb")}])
        assert result[0]["path"] == "mesh_a.glb"
        assert result[0]["type"] == "glb"


class TestErrorCases:

    def test_unsupported_type_raises(self):
        comp = make_component()
        with pytest.raises(ValueError, match="Unsupported asset type"):
            comp._validate_assets([{"path": "a.obj", "type": "obj"}])

    def test_missing_path_raises(self):
        comp = make_component()
        with pytest.raises(ValueError, match="missing required field 'path'"):
            comp._validate_assets([{"type": "ply"}])

    def test_empty_path_raises(self):
        comp = make_component()
        with pytest.raises(ValueError, match="missing required field 'path'"):
            comp._validate_assets([{"path": "", "type": "ply"}])

    def test_missing_type_raises_for_unknown_extension(self):
        comp = make_component()
        with pytest.raises(ValueError, match="Provide the 'type' explicitly"):
            comp._validate_assets([{"path": "a.unknown"}])

    def test_invalid_color_length_raises(self):
        comp = make_component()
        with pytest.raises(ValueError, match="invalid color"):
            comp._validate_assets([{"path": "a.ply", "type": "ply", "color": [255, 128]}])

    def test_too_many_assets_raises(self):
        comp = make_component(max_views=4)
        assets = [{"path": f"a{i}.ply", "type": "ply"} for i in range(6)]
        with pytest.raises(ValueError, match="max_views=4"):
            comp._validate_assets(assets)

    def test_max_views_boundary_accepted(self):
        comp = make_component(max_views=4)
        assets = [{"path": f"a{i}.ply", "type": "ply"} for i in range(4)]
        result = comp._validate_assets(assets)
        assert len(result) == 4

    def test_non_dict_asset_raises(self):
        comp = make_component()
        with pytest.raises(ValueError, match="must be a dict"):
            comp._validate_assets(["not_a_dict"])


class TestPostprocess:

    def test_postprocess_none_returns_none(self):
        comp = make_component()
        result = comp.postprocess(None)
        assert result is None

    def test_postprocess_valid_returns_dict(self):
        comp = make_component()
        result = comp.postprocess([{"path": "a.ply", "type": "ply"}])
        assert isinstance(result, dict)
        assert "assets" in result
        assert result["render_mode"] == "points"
        assert result["sync_camera"] is True
        assert result["point_size"] == 2.0
        assert result["max_point_size"] == 10.0
        assert result["height"] == 500
        assert result["default_zoom"] == 1.0
        assert result["min_zoom"] == 0.5
        assert result["max_zoom"] == 16.0

    def test_postprocess_invalid_raises(self):
        comp = make_component()
        with pytest.raises(ValueError):
            comp.postprocess([{"path": "a.obj", "type": "obj"}])

    def test_postprocess_reuses_existing_url(self):
        comp = make_component()
        result = comp.postprocess(
            [{"path": "https://example.com/a.glb", "type": "glb", "url": "https://example.com/a.glb"}]
        )
        assert result["assets"][0]["url"] == "https://example.com/a.glb"


class TestPreprocess:

    def test_preprocess_none(self):
        comp = make_component()
        assert comp.preprocess(None) is None

    def test_preprocess_dict_with_assets(self):
        comp = make_component()
        payload = {"assets": [{"path": "a.ply", "type": "ply"}]}
        result = comp.preprocess(payload)
        assert result == payload["assets"]

    def test_preprocess_passthrough(self):
        comp = make_component()
        data = [{"path": "a.ply", "type": "ply"}]
        result = comp.preprocess(data)
        assert result == data


class TestInit:

    def test_num_views_alias_sets_max_views(self):
        comp = Sync3DCompare(num_views=2)
        assert comp.max_views == 2

    def test_zoom_kwargs_are_preserved(self):
        comp = Sync3DCompare(default_zoom=2.0, min_zoom=0.75, max_zoom=12.0)
        assert comp.default_zoom == 2.0
        assert comp.min_zoom == 0.75
        assert comp.max_zoom == 12.0

    def test_max_point_size_is_preserved(self):
        comp = Sync3DCompare(point_size=6.0, max_point_size=18.0)
        assert comp.point_size == 6.0
        assert comp.max_point_size == 18.0

    def test_point_size_cannot_exceed_max_point_size(self):
        with pytest.raises(ValueError, match="point_size must be less than or equal to max_point_size"):
            Sync3DCompare(point_size=12.0, max_point_size=10.0)

    def test_point_size_floor_is_enforced(self):
        with pytest.raises(ValueError, match="must be at least 0.5"):
            Sync3DCompare(point_size=0.25)
