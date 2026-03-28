"""
Backend tests for Sync3DCompare component.
Tests validation logic, postprocessing, and error cases.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from gradio_sync3dcompare import Sync3DCompare


def make_component(**kwargs):
    """Create a Sync3DCompare instance, bypassing Gradio Component __init__ side effects."""
    comp = object.__new__(Sync3DCompare)
    comp.render_mode = kwargs.get("render_mode", "points")
    comp.sync_camera = kwargs.get("sync_camera", True)
    comp.point_size = kwargs.get("point_size", 2.0)
    comp.height = kwargs.get("height", 500)
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

    def test_missing_type_raises(self):
        comp = make_component()
        with pytest.raises(ValueError, match="missing required field 'type'"):
            comp._validate_assets([{"path": "a.ply"}])

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
        assert result["height"] == 500

    def test_postprocess_invalid_raises(self):
        comp = make_component()
        with pytest.raises(ValueError):
            comp.postprocess([{"path": "a.obj", "type": "obj"}])


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
