# Release Notes — gradio_sync3dcompare

---

# 🎉 gradio_sync3dcompare v0.0.8

Initial release of the synchronized 3D comparison viewer for Gradio.

## ✨ New: 3D Viewer Component

**Features**
- 🖼️ Synchronized side-by-side 3D comparison viewer as a Gradio custom component
- 📦 Supports **PLY** point cloud files and **GLB** mesh files (up to 4 viewports)
- 🔄 Two render modes:
  - `points` — renders PLY directly; samples GLB surface to a point cloud for fair comparison
  - `native` — renders GLB with full PBR materials and lighting
- 🎥 Camera synchronization across all viewports (orbit, pan, zoom) with `isSyncing` lock to prevent feedback loops
- 📐 Shared auto-camera based on global bounding box of all loaded assets
- 🎛️ Toolbar controls: Reset camera · Points/Native toggle · Point-size slider
- 🏷️ Per-asset configuration: `name`, `color [R,G,B]`, `visible`, `metadata`
- ✅ Backend validation: type checking, path validation, color validation, `max_views` enforcement
- 🌐 Gradio file-serving integration (`serve_static_file`) so browser can fetch assets via `/gradio_api/file=`

## 🛠️ Tech Stack

- 🐍 Python backend: Gradio 6.x custom component
- ⚡ Frontend: Svelte 5 + TypeScript + Three.js r170
- 📂 Loaders: `PLYLoader`, `GLTFLoader` (supports `KHR_materials_specular`)
- 🔵 GLB→points: area-weighted surface sampling (`MeshSurfaceSampler`-style)

## ⚠️ Known Limitations

- Maximum 4 viewports (MVP constraint)
- No DRACO-compressed GLB support yet
- `gradio cc dev` hot-reload incompatible with Node.js v24 (use `python demo_sync.py` instead)

