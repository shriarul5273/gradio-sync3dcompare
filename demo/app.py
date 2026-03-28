import gradio as gr
from gradio_sync3dcompare import Sync3DCompare


with gr.Blocks(title="Sync3DCompare Demo") as demo:
    gr.Markdown("# Sync3DCompare — Synchronized 3D Comparison Viewer")
    gr.Markdown(
        "Compare two 3D assets side-by-side with synchronized orbit, pan, and zoom. "
        "Rotate one view and all others follow."
    )
    gr.Markdown(
        "### Two synchronized viewports. Upload `.ply` or `.glb` files manually into each pane."
    )
    Sync3DCompare(
        label="Two-Viewport 3D Comparison",
        value=[],
        render_mode="points",
        sync_camera=True,
        point_size=2.0,
        height=540,
        max_views=2,
    )


if __name__ == "__main__":
    demo.launch()
