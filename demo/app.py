import gradio as gr
from gradio_sync3dcompare import Sync3DCompare
import os

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

def get_path(filename):
    return os.path.join(SAMPLE_DIR, filename)


with gr.Blocks(title="Sync3DCompare Demo") as demo:
    gr.Markdown("# Sync3DCompare — Synchronized 3D Comparison Viewer")
    gr.Markdown(
        "Compare 3D reconstruction outputs side-by-side with synchronized orbit, pan, and zoom. "
        "Rotate one view and all others follow."
    )

    with gr.Tabs():

        # --- Tab A: PLY comparison ---
        with gr.TabItem("PLY Comparison"):
            gr.Markdown("### Three PLY point clouds compared side-by-side")
            Sync3DCompare(
                label="PLY Comparison",
                value=[
                    {
                        "name": "Ground Truth",
                        "path": get_path("ground_truth.ply"),
                        "type": "ply",
                        "color": [80, 200, 120],
                    },
                    {
                        "name": "Method A",
                        "path": get_path("method_a.ply"),
                        "type": "ply",
                        "color": [100, 160, 240],
                    },
                    {
                        "name": "Method B",
                        "path": get_path("method_b.ply"),
                        "type": "ply",
                        "color": [240, 140, 80],
                    },
                ],
                render_mode="points",
                sync_camera=True,
                point_size=2.0,
                height=500,
            )

        # --- Tab B: GLB comparison ---
        with gr.TabItem("GLB Comparison"):
            gr.Markdown("### Two GLB mesh outputs compared in native mode")
            Sync3DCompare(
                label="GLB Comparison",
                value=[
                    {
                        "name": "Mesh A (detailed)",
                        "path": get_path("mesh_a.glb"),
                        "type": "glb",
                    },
                    {
                        "name": "Mesh B (coarse)",
                        "path": get_path("mesh_b.glb"),
                        "type": "glb",
                    },
                ],
                render_mode="native",
                sync_camera=True,
                point_size=2.0,
                height=500,
            )

        # --- Tab C: Mixed PLY + GLB ---
        with gr.TabItem("Mixed Format (Points Mode)"):
            gr.Markdown(
                "### PLY + GLB compared in `points` mode — GLB is sampled to point cloud for fair comparison"
            )
            Sync3DCompare(
                label="Mixed Format Comparison",
                value=[
                    {
                        "name": "PLY Point Cloud",
                        "path": get_path("ground_truth.ply"),
                        "type": "ply",
                        "color": [80, 200, 120],
                    },
                    {
                        "name": "GLB as Points",
                        "path": get_path("mesh_a.glb"),
                        "type": "glb",
                    },
                ],
                render_mode="points",
                sync_camera=True,
                point_size=3.0,
                height=500,
            )


if __name__ == "__main__":
    demo.launch()
