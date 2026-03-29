from pathlib import Path

import gradio as gr

from gradio_sync3dcompare import Sync3DCompare


ROOT = Path(__file__).resolve().parent
SAMPLE_DIR = (ROOT / "demo" / "sample_data").resolve()
MESH_A = SAMPLE_DIR / "mesh_a.glb"
MESH_B = SAMPLE_DIR / "mesh_b.glb"
POINT_SIZE = 2
DEFAULT_ZOOM = 1.0
MIN_ZOOM = 2.5
MAX_ZOOM = 16.0


def load_comparison():
    return [
        {"name": "Mesh A", "path": str(MESH_A), "type": "glb"},
        {"name": "Mesh B", "path": str(MESH_B), "type": "glb"},
    ]


with gr.Blocks(title="Synchronized GLB and PLY Comparison") as demo:
    gr.Markdown("# Synchronized GLB and PLY Comparison")
    gr.Markdown(
        "The component supports both GLB and PLY files. Click the button to load two sample GLB files into a side-by-side viewer with synchronized orbit, zoom, and pan."
    )

    viewer = Sync3DCompare(
        value=[],
        label="3D Comparison",
        render_mode="points",
        sync_camera=True,
        point_size=POINT_SIZE,
        max_point_size= 60,
        default_zoom=DEFAULT_ZOOM,
        min_zoom=MIN_ZOOM,
        max_zoom=MAX_ZOOM,
        height=500,
        num_views=2,
    )
    load_button = gr.Button("Load Comparison", variant="primary")
    load_button.click(fn=load_comparison, outputs=viewer)


if __name__ == "__main__":
    demo.launch(allowed_paths=[str(SAMPLE_DIR)])
