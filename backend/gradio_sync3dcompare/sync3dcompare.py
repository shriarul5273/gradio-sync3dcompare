from __future__ import annotations

import os
from typing import Any, Literal

from gradio.components.base import Component
from gradio.data_classes import GradioModel
from pydantic import field_validator

MIN_POINT_SIZE = 0.5


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
    point_size_mode: Literal["auto", "manual"] = "auto"
    point_size: float = 1.0
    max_point_size: float = 10.0
    height: int = 500
    default_zoom: float = 1.0
    min_zoom: float = 0.5
    max_zoom: float = 16.0


class Sync3DCompare(Component):
    """
    A Gradio custom component for synchronized comparison of 3D reconstruction outputs.
    Supports up to 4 PLY and GLB files, displayed side-by-side with synchronized camera movement.

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
        point_size_mode: Literal["auto", "manual"] = "auto",
        point_size: float = 1.0,
        max_point_size: float = 10.0,
        default_zoom: float = 1.0,
        min_zoom: float = 0.5,
        max_zoom: float = 16.0,
        height: int = 500,
        max_views: int = 4,
        num_views: int | None = None,
        interactive: bool = True,
        visible: bool = True,
        elem_id: str | None = None,
        elem_classes: list[str] | str | None = None,
        render: bool = True,
        **kwargs,
    ):
        if num_views is not None:
            max_views = num_views

        if min_zoom <= 0 or max_zoom <= 0:
            raise ValueError("min_zoom and max_zoom must be positive.")
        if min_zoom > max_zoom:
            raise ValueError("min_zoom must be less than or equal to max_zoom.")
        if point_size < MIN_POINT_SIZE or max_point_size < MIN_POINT_SIZE:
            raise ValueError(
                f"point_size and max_point_size must be at least {MIN_POINT_SIZE}."
            )
        if point_size > max_point_size:
            raise ValueError("point_size must be less than or equal to max_point_size.")

        self.render_mode = render_mode
        self.sync_camera = sync_camera
        self.point_size_mode = point_size_mode
        self.point_size = point_size
        self.max_point_size = max_point_size
        self.default_zoom = min(max(default_zoom, min_zoom), max_zoom)
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
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

    @staticmethod
    def _coerce_path(path: Any) -> str:
        if isinstance(path, os.PathLike):
            return os.fspath(path)
        if path is None:
            return ""
        return str(path)

    @staticmethod
    def _infer_asset_type(path: str) -> Literal["ply", "glb"] | None:
        suffix = os.path.splitext(path)[1].lower()
        if suffix == ".ply":
            return "ply"
        if suffix == ".glb":
            return "glb"
        return None

    def _validate_assets(self, value: list[dict]) -> list[dict]:
        if len(value) > self.max_views:
            raise ValueError(
                f"Received {len(value)} assets, but max_views={self.max_views} for the MVP."
            )

        validated = []
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                raise ValueError(f"Asset at index {i} must be a dict.")

            path = self._coerce_path(item.get("path"))
            if not path:
                raise ValueError(f"Asset at index {i} is missing required field 'path'.")

            asset_type = item.get("type") or self._infer_asset_type(path)
            if asset_type not in ("ply", "glb"):
                raise ValueError(
                    f"Unsupported asset type: '{asset_type}' at index {i}. "
                    f"Supported types are: ply, glb. "
                    "Provide the 'type' explicitly or use a .ply/.glb path."
                )

            color = item.get("color")
            if color is not None and len(color) != 3:
                raise ValueError(
                    f"Asset at index {i} has invalid color. Expected [R, G, B]."
                )

            normalized = {
                "name": item.get("name") or f"Asset {i + 1}",
                "path": path,
                "type": asset_type,
                "visible": item.get("visible", True),
                "color": color,
                "metadata": item.get("metadata"),
                "url": item.get("url"),
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
            asset_url = asset.get("url")
            if isinstance(asset_url, str) and asset_url:
                continue

            path = asset["path"]
            if path.startswith(("http://", "https://", "/gradio_api/")):
                asset["url"] = path
            else:
                file_info = self.serve_static_file(path)
                if file_info and isinstance(file_info, dict):
                    # file_info = {"path": "...", "url": "/gradio_api/file=..."}
                    asset["url"] = file_info.get("url") or file_info.get("path")
                else:
                    asset["url"] = path

        return {
            "assets": validated,
            "render_mode": self.render_mode,
            "sync_camera": self.sync_camera,
            "point_size_mode": self.point_size_mode,
            "point_size": self.point_size,
            "max_point_size": self.max_point_size,
            "height": self.height,
            "default_zoom": self.default_zoom,
            "min_zoom": self.min_zoom,
            "max_zoom": self.max_zoom,
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

    @staticmethod
    def _asset_schema() -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "path": {"type": "string"},
                "url": {"type": "string"},
                "type": {"type": "string", "enum": ["ply", "glb"]},
                "visible": {"type": "boolean"},
                "color": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 3,
                    "maxItems": 3,
                },
                "metadata": {"type": "object", "additionalProperties": True},
            },
            "required": ["path"],
        }

    def api_info_as_input(self):
        return {
            "type": "array",
            "items": self._asset_schema(),
            "description": (
                "List of up to 4 asset descriptors. Each item requires a path and supports "
                "an optional type (ply|glb), name, visible flag, color [R,G,B], "
                "metadata, and a pre-served url."
            ),
        }

    def api_info_as_output(self):
        return {
            "type": "object",
            "properties": {
                "assets": {
                    "type": "array",
                    "items": self._asset_schema(),
                },
                "render_mode": {"type": "string", "enum": ["points", "native"]},
                "sync_camera": {"type": "boolean"},
                "point_size_mode": {"type": "string", "enum": ["auto", "manual"]},
                "point_size": {"type": "number"},
                "max_point_size": {"type": "number"},
                "height": {"type": "integer"},
                "default_zoom": {"type": "number"},
                "min_zoom": {"type": "number"},
                "max_zoom": {"type": "number"},
            },
            "required": [
                "assets",
                "render_mode",
                "sync_camera",
                "point_size_mode",
                "point_size",
                "max_point_size",
                "height",
                "default_zoom",
                "min_zoom",
                "max_zoom",
            ],
            "description": (
                "Rendered Sync3DCompare payload with up to 4 validated assets, "
                "served URLs, and viewer settings including zoom bounds."
            ),
        }

    def api_info(self):
        return self.api_info_as_output()
