
import gradio as gr
from app import demo as app
import os

_docs = {'Sync3DCompare': {'description': 'A Gradio custom component for synchronized comparison of 3D reconstruction outputs.\nSupports up to 4 PLY and GLB files, displayed side-by-side with synchronized camera movement.\n', 'members': {'__init__': {'value': {'type': 'list[dict]| None', 'default': 'value = None', 'description': None}, 'label': {'type': 'str| None', 'default': 'value = "3D Comparison"', 'description': None}, 'render_mode': {'type': '"points"| "native"', 'default': 'value = "points"', 'description': None}, 'sync_camera': {'type': 'bool', 'default': 'value = True', 'description': None}, 'point_size': {'type': 'float', 'default': 'value = 2.0', 'description': None}, 'max_point_size': {'type': 'float', 'default': 'value = 10.0', 'description': None}, 'default_zoom': {'type': 'float', 'default': 'value = 1.0', 'description': None}, 'min_zoom': {'type': 'float', 'default': 'value = 0.5', 'description': None}, 'max_zoom': {'type': 'float', 'default': 'value = 16.0', 'description': None}, 'height': {'type': 'int', 'default': 'value = 500', 'description': None}, 'max_views': {'type': 'int', 'default': 'value = 4', 'description': None}, 'num_views': {'type': 'int| None', 'default': 'value = None', 'description': None}, 'interactive': {'type': 'bool', 'default': 'value = True', 'description': None}, 'visible': {'type': 'bool', 'default': 'value = True', 'description': None}, 'elem_id': {'type': 'str| None', 'default': 'value = None', 'description': None}, 'elem_classes': {'type': 'list[str]| str| None', 'default': 'value = None', 'description': None}, 'render': {'type': 'bool', 'default': 'value = True', 'description': None}}, 'postprocess': {'value': {'type': 'list[dict]| None', 'description': "The output data received by the component from the user's function in the backend."}}, 'preprocess': {}}, 'events': {'change': {'type': None, 'default': None, 'description': ''}}}, '__meta__': {'additional_interfaces': {}, 'user_fn_refs': {'Sync3DCompare': []}}}

abs_path = os.path.join(os.path.dirname(__file__), "css.css")

with gr.Blocks(
    css=abs_path,
    theme=gr.themes.Default(
        font_mono=[
            gr.themes.GoogleFont("Inconsolata"),
            "monospace",
        ],
    ),
) as demo:
    gr.Markdown(
"""
# `gradio_sync3dcompare`

<div style="display: flex; gap: 7px;">
<a href="https://pypi.org/project/gradio_sync3dcompare/" target="_blank"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/gradio_sync3dcompare"></a> <a href="https://github.com/shriarul5273/gradio-sync3dcompare/issues" target="_blank"><img alt="Static Badge" src="https://img.shields.io/badge/Issues-white?logo=github&logoColor=black"></a> 
</div>

Synchronized side-by-side 3D comparison viewer for Gradio — supports PLY and GLB files with shared camera control.
""", elem_classes=["md-custom"], header_links=True)
    app.render()
    gr.Markdown(
"""
## Installation

```bash
pip install gradio_sync3dcompare
```

## Usage

```python
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

```
""", elem_classes=["md-custom"], header_links=True)


    gr.Markdown("""
## `Sync3DCompare`

### Initialization
""", elem_classes=["md-custom"], header_links=True)

    gr.ParamViewer(value=_docs["Sync3DCompare"]["members"]["__init__"], linkify=[])


    gr.Markdown("### Events")
    gr.ParamViewer(value=_docs["Sync3DCompare"]["events"], linkify=['Event'])




    gr.Markdown("""

### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As output:** Should return, the output data received by the component from the user's function in the backend.

 ```python
def predict(
    value: Unknown
) -> list[dict]| None:
    return value
```
""", elem_classes=["md-custom", "Sync3DCompare-user-fn"], header_links=True)




    demo.load(None, js=r"""function() {
    const refs = {};
    const user_fn_refs = {
          Sync3DCompare: [], };
    requestAnimationFrame(() => {

        Object.entries(user_fn_refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}-user-fn`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })

        Object.entries(refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })
    })
}

""")

demo.launch()
