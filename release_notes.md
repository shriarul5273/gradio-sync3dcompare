# Release Notes — gradio_sync3dcompare
<a href="https://huggingface.co/spaces/shriarul5273/gradio_sync3dcompare_demo" target="_blank"><img alt="Hugging Face Spaces" src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue"></a>
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/gradio-sync3dcompare?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/gradio-sync3dcompare)
---

# 🎉 gradio_sync3dcompare v0.0.12

This release focuses on stabilizing the custom component workflow, clarifying demo behavior, and improving local file handling for PLY and GLB assets.

## ✨ Improvements

**Backend**
- Added support for both `max_views` and `num_views` when configuring the component
- Added automatic asset-type inference from `.ply` and `.glb` file extensions when `type` is omitted
- Improved local file handling by normalizing filesystem paths and serving browser-safe URLs through Gradio's `serve_static_file()`
- Kept validation for asset shape, color values, and viewport-count limits

**Frontend**
- Preserved synchronized orbit, pan, and zoom across side-by-side viewports
- Continued support for both `points` and `native` render modes
- Improved component prop wiring so runtime updates from Gradio events are passed through consistently

**Demos**
- Simplified `demo/app.py` to a 2-viewport comparison demo with manual `.ply` / `.glb` upload
- Added a button-driven `demo_sync.py` example that loads two GLB files from `demo/sample_data`
- Kept the component itself compatible with up to 4 viewports even though the main demo now shows 2 by default

## 🛠️ Development Notes

- `gradio cc dev` should be run from the same checkout that is installed in editable mode
- If multiple local copies of the repo exist, Vite may fail with a `server.fs.allow` path error if Gradio resolves the frontend from a different checkout
- Node.js 20 or 22 remains the safer choice for custom-component development; Node.js 24 has been unreliable in local dev mode

## ⚠️ Known Limitations

- Maximum 4 viewports
- No DRACO-compressed GLB support yet
- GLB rendering behavior depends on the selected mode:
  - `native` renders the mesh directly
  - `points` converts GLB geometry into a sampled point cloud
