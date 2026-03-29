<script lang="ts">
  import { onMount } from "svelte";
  import * as THREE from "three";
  import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
  import type { LoadedAsset } from "./assetLoader.js";
  import { resolvePointSize } from "./pointSizing.js";
  import type { CameraState, PointSizeMode } from "../types";
  import type { CameraSyncManager } from "./cameraSyncManager.js";

  interface Props {
    asset: LoadedAsset | null;
    label: string;
    height: number;
    syncManager: CameraSyncManager;
    initialCamera: CameraState | null;
    pointSizeMode: PointSizeMode;
    pointSize: number;
    loading: boolean;
    error: string | null;
    placeholder?: boolean;
    uploadable?: boolean;
    request_upload?: () => void;
    drop_files?: (files: File[]) => void;
    removable?: boolean;
    remove_asset?: () => void;
  }

  let {
    asset,
    label,
    height,
    syncManager,
    initialCamera,
    pointSizeMode,
    pointSize,
    loading,
    error,
    placeholder = false,
    uploadable = false,
    request_upload,
    drop_files,
    removable = false,
    remove_asset,
  }: Props = $props();

  let canvasEl: HTMLCanvasElement;
  const viewportId = crypto.randomUUID();

  // Use $state so effects can track when the Three.js objects are ready
  let renderer = $state<THREE.WebGLRenderer | null>(null);
  let scene    = $state<THREE.Scene | null>(null);
  let camera   = $state<THREE.PerspectiveCamera | null>(null);
  let controls = $state<OrbitControls | null>(null);

  let animFrameId: number | null = null;
  let resizeObserver: ResizeObserver | null = null;
  let currentObject: THREE.Object3D | null = null;

  // ─── Three.js init (runs once after DOM mount) ────────────────────────────
  onMount(() => {
    initRenderer();
    return () => dispose();
  });

  function initRenderer() {
    if (!canvasEl) return;

    const _renderer = new THREE.WebGLRenderer({ canvas: canvasEl, antialias: true });
    _renderer.setPixelRatio(window.devicePixelRatio);
    _renderer.setClearColor(0x1a1a2e);

    const _scene = new THREE.Scene();
    _scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const dir = new THREE.DirectionalLight(0xffffff, 0.5);
    dir.position.set(5, 10, 7);
    _scene.add(dir);

    const w = canvasEl.clientWidth || canvasEl.offsetWidth || 300;
    const h = height;
    const _camera = new THREE.PerspectiveCamera(60, Math.max(w, 1) / h, 0.001, 100000);

    const _controls = new OrbitControls(_camera, _renderer.domElement);
    _controls.enableDamping = true;
    _controls.dampingFactor = 0.1;

    // Set state — this triggers the reactive effects below
    renderer = _renderer;
    scene    = _scene;
    camera   = _camera;
    controls = _controls;

    resizeObserver = new ResizeObserver(() => onResize());
    resizeObserver.observe(canvasEl.parentElement!);
    onResize();
    startLoop();
  }

  // ─── Add/swap asset whenever scene or asset changes ───────────────────────
  $effect(() => {
    const s = scene;
    const a = asset;  // always read both so Svelte tracks both
    if (!s) return;

    if (currentObject) {
      s.remove(currentObject);
      currentObject = null;
    }
    if (a?.object3d) {
      s.add(a.object3d);
      currentObject = a.object3d;
    }
    renderFrame();
  });

  // ─── Apply initial camera whenever camera/controls/initialCamera are ready ─
  $effect(() => {
    const cam  = camera;
    const ctrl = controls;
    const ic   = initialCamera;  // always read all three
    if (!cam || !ctrl || !ic) return;

    cam.position.set(ic.position.x, ic.position.y, ic.position.z);
    cam.up.set(ic.up.x, ic.up.y, ic.up.z);
    cam.zoom = 1;
    if (ic.near !== undefined) {
      cam.near = ic.near;
    }
    if (ic.far !== undefined) {
      cam.far = ic.far;
    }
    cam.updateProjectionMatrix();
    ctrl.target.set(ic.target.x, ic.target.y, ic.target.z);
    ctrl.update();
    renderFrame();
  });

  // ─── Sync camera registration whenever controls/camera change ─────────────
  $effect(() => {
    const cam  = camera;
    const ctrl = controls;
    if (!cam || !ctrl) return;
    // Re-register in case the syncManager needs fresh refs
    syncManager.register({ id: viewportId, camera: cam, controls: ctrl, render: renderFrame });
  });

  // ─── Update point size live ───────────────────────────────────────────────
  $effect(() => {
    const a = asset;
    const mode = pointSizeMode;
    const ps = pointSize;
    if (!a?.object3d) return;

    const resolvedSize = resolvePointSize(mode, ps, a.basePointSize);
    if (resolvedSize === null) return;

    a.object3d.traverse((child) => {
      const pts = child as THREE.Points;
      if (pts.isPoints && pts.material) {
        (pts.material as THREE.PointsMaterial).size = resolvedSize;
      }
    });
    renderFrame();
  });

  // ─── Helpers ──────────────────────────────────────────────────────────────
  function renderFrame() {
    if (!renderer || !scene || !camera) return;
    renderer.render(scene, camera);
  }

  function onResize() {
    if (!canvasEl || !renderer || !camera) return;
    const parent = canvasEl.parentElement;
    if (!parent) return;
    const w = parent.clientWidth || parent.offsetWidth;
    if (w === 0) {
      // Tab is hidden — retry on next frame
      requestAnimationFrame(() => onResize());
      return;
    }
    const h = height;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderFrame();
  }

  function startLoop() {
    function loop() {
      animFrameId = requestAnimationFrame(loop);
      controls?.update();
      // If canvas has no size yet, keep retrying resize
      if (renderer && canvasEl) {
        const w = canvasEl.parentElement?.clientWidth ?? 0;
        if (w > 0 && renderer.domElement.width === 0) onResize();
      }
      renderFrame();
    }
    loop();
  }

  function dispose() {
    if (animFrameId !== null) cancelAnimationFrame(animFrameId);
    syncManager.unregister(viewportId);
    controls?.dispose();
    renderer?.dispose();
    resizeObserver?.disconnect();
  }

  function handlePlaceholderDrop(event: DragEvent) {
    event.preventDefault();
    if (!drop_files) return;
    const files = Array.from(event.dataTransfer?.files ?? []);
    if (files.length > 0) {
      drop_files(files);
    }
  }

  function handlePlaceholderDragOver(event: DragEvent) {
    event.preventDefault();
  }
</script>

<div class="viewport-wrapper" style="height: {height}px; position: relative;">
  {#if !placeholder}
    <div class="viewport-header">
      {#if removable}
        <button
          class="viewport-remove-btn"
          type="button"
          onclick={remove_asset}
          aria-label={`Remove ${label}`}
          title={`Remove ${label}`}
        >
          ×
        </button>
      {/if}
      <div class="viewport-label">{label}</div>
    </div>
  {/if}

  {#if loading}
    <div class="overlay loading-overlay">
      <div class="spinner"></div>
      <span>Loading…</span>
    </div>
  {/if}

  {#if error}
    <div class="overlay error-overlay">
      <span>⚠ {error}</span>
    </div>
  {/if}

  {#if placeholder && !loading && !error}
    <div class="placeholder-frame" aria-hidden="true"></div>
    <button
      class="overlay placeholder-overlay placeholder-button"
      type="button"
      onclick={request_upload}
      ondragover={handlePlaceholderDragOver}
      ondrop={handlePlaceholderDrop}
      disabled={!uploadable}
      aria-label="Upload a .ply or .glb file"
    >
      <div class="placeholder-icon">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M12 16V6m0 0-4 4m4-4 4 4M5 19h14"
            fill="none"
            stroke="currentColor"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.7"
          />
        </svg>
      </div>
      <span class="placeholder-title">Upload</span>
      <span class="placeholder-subtitle">.ply / .glb</span>
    </button>
  {/if}

  <canvas
    bind:this={canvasEl}
    class:placeholder-canvas={placeholder && !loading && !error}
    style="width:100%; height:{height}px; display:block;"
  ></canvas>
</div>

<style>
  .viewport-wrapper {
    position: relative;
    background: linear-gradient(180deg, #1f223d 0%, #1a1d35 100%);
    border: 1px solid #2e3353;
    border-radius: 10px;
    overflow: hidden;
    flex: 1 1 0;
    min-width: 0;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
  }
  .viewport-label {
    background: rgba(9, 12, 26, 0.78);
    color: #d8def6;
    font-size: 12px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    padding: 4px 9px;
    border-radius: 999px;
    border: 1px solid rgba(125, 140, 192, 0.28);
    pointer-events: none;
  }
  .viewport-header {
    position: absolute;
    top: 12px;
    left: 12px;
    z-index: 10;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    pointer-events: none;
  }
  .viewport-remove-btn {
    width: 24px;
    height: 24px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(125, 140, 192, 0.36);
    border-radius: 999px;
    background: rgba(9, 12, 26, 0.88);
    color: #d8def6;
    font-size: 16px;
    line-height: 1;
    cursor: pointer;
    pointer-events: auto;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
  }
  .viewport-remove-btn:hover {
    background: rgba(126, 42, 42, 0.92);
    border-color: rgba(255, 129, 129, 0.46);
    color: #fff1f1;
  }
  .viewport-remove-btn:focus-visible {
    outline: 2px solid #7da2ff;
    outline-offset: 2px;
  }
  .overlay {
    position: absolute;
    inset: 0;
    z-index: 20;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    font-size: 13px;
    font-family: ui-sans-serif, system-ui, sans-serif;
    pointer-events: none;
  }
  .loading-overlay { background: rgba(20, 24, 44, 0.82); color: #a9b3d9; }
  .error-overlay   { background: rgba(80,20,20,0.85);  color: #ff8888; }
  .placeholder-overlay {
    color: #7c88b8;
    gap: 6px;
    pointer-events: auto;
  }
  .placeholder-button {
    border: 0;
    background: transparent;
    width: 100%;
    height: 100%;
    cursor: pointer;
  }
  .placeholder-button:disabled {
    cursor: default;
  }
  .placeholder-button:focus-visible {
    outline: 2px solid #7da2ff;
    outline-offset: -12px;
  }
  .placeholder-frame {
    position: absolute;
    inset: 10px;
    border: 1px dashed rgba(124, 136, 184, 0.42);
    border-radius: 8px;
    pointer-events: none;
  }
  .placeholder-icon {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    border-radius: 999px;
    border: 1px solid rgba(124, 136, 184, 0.3);
    background: rgba(18, 22, 43, 0.42);
  }
  .placeholder-icon svg {
    width: 22px;
    height: 22px;
  }
  .placeholder-title {
    color: #9aa7dc;
    font-size: 13px;
    font-weight: 500;
  }
  .placeholder-subtitle {
    color: #65719f;
    font-size: 11px;
    letter-spacing: 0.02em;
  }
  .placeholder-canvas {
    opacity: 0;
  }
  .spinner {
    width: 28px; height: 28px;
    border: 3px solid #444;
    border-top-color: #7eb8f7;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
