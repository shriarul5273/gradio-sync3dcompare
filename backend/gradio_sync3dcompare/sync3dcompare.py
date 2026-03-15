from __future__ import annotations

from typing import Any, Literal

from gradio.components.base import Component
from gradio.data_classes import GradioModel
from pydantic import field_validator, model_validator


class AssetItem(GradioModel):
    name: str | None = None
    path: str
    type: Literal["ply", "glb"]
    visible: bool = True
    color: list[int] | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: list[int] | None) -> list[int] | None:
        if v is not None and len(v) != 3:
            raise ValueError("color must be a list of 3 integers [R, G, B]")
        return v


class Sync3DCompareData(GradioModel):
    assets: list[AssetItem]
    render_mode: Literal["points", "native"] = "points"
    sync_camera: bool = True
    point_size: float = 2.0
    height: int = 500


class Sync3DCompare(Component):
    """
    A Gradio custom component for synchronized comparison of 3D reconstruction outputs.
    Supports PLY and GLB files, displayed side-by-side with synchronized camera movement.

    Demos: demo
    """

    EVENTS = ["change"]

    def __init__(
        self,
        value: list[dict] | None = None,
        *,
        label: str | None = "3D Comparison",
        render_mode: Literal["points", "native"] = "points",
        sync_camera: bool = True,
        point_size: float = 2.0,
        height: int = 500,
        max_views: int = 4,
        interactive: bool = True,
        visible: bool = True,
        elem_id: str | None = None,
        elem_classes: list[str] | str | None = None,
        render: bool = True,
        **kwargs,
    ):
        self.render_mode = render_mode
        self.sync_camera = sync_camera
        self.point_size = point_size
        self.height = height
        self.max_views = max_views

        super().__init__(
            value=value,
            label=label,
            interactive=interactive,
            visible=visible,
            elem_id=elem_id,
            elem_classes=elem_classes,
            render=render,
            **kwargs,
        )

    def _validate_assets(self, value: list[dict]) -> list[dict]:
        if len(value) > self.max_views:
            raise ValueError(
                f"Received {len(value)} assets, but max_views={self.max_views} for the MVP."
            )

        validated = []
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                raise ValueError(f"Asset at index {i} must be a dict.")

            if "path" not in item or not item["path"]:
                raise ValueError(f"Asset at index {i} is missing required field 'path'.")

            if "type" not in item:
                raise ValueError(f"Asset at index {i} is missing required field 'type'.")

            asset_type = item["type"]
            if asset_type not in ("ply", "glb"):
                raise ValueError(
                    f"Unsupported asset type: '{asset_type}' at index {i}. "
                    f"Supported types are: ply, glb."
                )

            color = item.get("color")
            if color is not None and len(color) != 3:
                raise ValueError(
                    f"Asset at index {i} has invalid color. Expected [R, G, B]."
                )

            normalized = {
                "name": item.get("name") or f"Asset {i + 1}",
                "path": item["path"],
                "type": asset_type,
                "visible": item.get("visible", True),
                "color": color,
                "metadata": item.get("metadata"),
            }
            validated.append(normalized)

        return validated

    def preprocess(self, payload):
        if payload is None:
            return None
        if isinstance(payload, dict) and "assets" in payload:
            return payload["assets"]
        return payload

    def postprocess(self, value: list[dict] | None):
        if value is None:
            return None
        validated = self._validate_assets(value)

        # Convert local filesystem paths to Gradio-served URLs so the browser can fetch them.
        for asset in validated:
            file_info = self.serve_static_file(asset["path"])
            if file_info and isinstance(file_info, dict):
                # file_info = {"path": "...", "url": "/gradio_api/file=..."}
                asset["url"] = file_info.get("url") or file_info.get("path")
            else:
                asset["url"] = asset["path"]

        return {
            "assets": validated,
            "render_mode": self.render_mode,
            "sync_camera": self.sync_camera,
            "point_size": self.point_size,
            "height": self.height,
        }

    def example_payload(self):
        return [
            {"name": "Example PLY", "path": "example.ply", "type": "ply"},
            {"name": "Example GLB", "path": "example.glb", "type": "glb"},
        ]

    def example_value(self):
        return [
            {"name": "Example PLY", "path": "example.ply", "type": "ply"},
            {"name": "Example GLB", "path": "example.glb", "type": "glb"},
        ]

    def api_info(self):
        return {
            "type": "array",
            "description": (
                "List of asset descriptors with keys: "
                "path (required), type (required: ply|glb), "
                "name, visible, color [R,G,B], metadata"
            ),
        }
