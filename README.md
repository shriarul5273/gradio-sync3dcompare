
# `gradio_sync3dcompare`
<a href="https://pypi.org/project/gradio_sync3dcompare/" target="_blank"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/gradio_sync3dcompare"></a> <a href="https://github.com/shriarul5273/gradio-sync3dcompare/issues" target="_blank"><img alt="Static Badge" src="https://img.shields.io/badge/Issues-white?logo=github&logoColor=black"></a><a href="https://huggingface.co/spaces/shriarul5273/gradio_sync3dcompare_demo" target="_blank"><img alt="Hugging Face Spaces" src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue"></a>

Synchronized side-by-side 3D comparison viewer for Gradio — supports PLY and GLB files with shared camera control.

## Installation

```bash
pip install gradio_sync3dcompare
```

## Usage

```python
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

```

## `Sync3DCompare`

### Initialization

<table>
<thead>
<tr>
<th align="left">name</th>
<th align="left" style="width: 25%;">type</th>
<th align="left">default</th>
<th align="left">description</th>
</tr>
</thead>
<tbody>
<tr>
<td align="left"><code>value</code></td>
<td align="left" style="width: 25%;">

```python
list[dict]| None
```

</td>
<td align="left"><code>value = None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>label</code></td>
<td align="left" style="width: 25%;">

```python
str| None
```

</td>
<td align="left"><code>value = "3D Comparison"</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>render_mode</code></td>
<td align="left" style="width: 25%;">

```python
"points"| "native"
```

</td>
<td align="left"><code>value = "points"</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>sync_camera</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>value = True</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>point_size</code></td>
<td align="left" style="width: 25%;">

```python
float
```

</td>
<td align="left"><code>value = 2.0</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>height</code></td>
<td align="left" style="width: 25%;">

```python
int
```

</td>
<td align="left"><code>value = 500</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>num_views</code></td>
<td align="left" style="width: 25%;">

```python
int
```

</td>
<td align="left"><code>value = 2</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>interactive</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>value = True</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>visible</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>value = True</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>elem_id</code></td>
<td align="left" style="width: 25%;">

```python
str| None
```

</td>
<td align="left"><code>value = None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>elem_classes</code></td>
<td align="left" style="width: 25%;">

```python
list[str]| str| None
```

</td>
<td align="left"><code>value = None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>render</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>value = True</code></td>
<td align="left">None</td>
</tr>
</tbody></table>


### Events

| name | description |
|:-----|:------------|
| `change` |  |



### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As input:** Should return, the output data received by the component from the user's function in the backend.

 ```python
 def predict(
     value: Unknown
 ) -> list[dict]| None:
     return value
 ```
 
