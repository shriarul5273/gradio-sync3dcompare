
# `gradio_sync3dcompare`
<a href="https://pypi.org/project/gradio_sync3dcompare/" target="_blank"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/gradio_sync3dcompare"></a> <a href="https://github.com/shriarul5273/gradio-sync3dcompare/issues" target="_blank"><img alt="Static Badge" src="https://img.shields.io/badge/Issues-white?logo=github&logoColor=black"></a><a href="https://huggingface.co/spaces/shriarul5273/gradio_sync3dcompare_demo" target="_blank"><img alt="Hugging Face Spaces" src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue"></a>
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/gradio-sync3dcompare?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/gradio-sync3dcompare)

Synchronized side-by-side 3D comparison viewer for Gradio — supports PLY and GLB files with shared camera control.

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
        point_size_mode="auto",
        point_size=1.0,
        height=540,
        max_views=2,
    )


if __name__ == "__main__":
    demo.launch(ssr_mode=False)

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
<td align="left"><code>point_size_mode</code></td>
<td align="left" style="width: 25%;">

```python
"auto"| "manual"
```

</td>
<td align="left"><code>value = "auto"</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>point_size</code></td>
<td align="left" style="width: 25%;">

```python
float
```

</td>
<td align="left"><code>value = 1.0</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>max_point_size</code></td>
<td align="left" style="width: 25%;">

```python
float
```

</td>
<td align="left"><code>value = 10.0</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>default_zoom</code></td>
<td align="left" style="width: 25%;">

```python
float
```

</td>
<td align="left"><code>value = 1.0</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>min_zoom</code></td>
<td align="left" style="width: 25%;">

```python
float
```

</td>
<td align="left"><code>value = 0.5</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>max_zoom</code></td>
<td align="left" style="width: 25%;">

```python
float
```

</td>
<td align="left"><code>value = 16.0</code></td>
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
<td align="left"><code>max_views</code></td>
<td align="left" style="width: 25%;">

```python
int
```

</td>
<td align="left"><code>value = 4</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>num_views</code></td>
<td align="left" style="width: 25%;">

```python
int| None
```

</td>
<td align="left"><code>value = None</code></td>
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
 
