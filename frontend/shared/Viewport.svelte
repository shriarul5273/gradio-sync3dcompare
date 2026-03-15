<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import * as THREE from "three";
  import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
  import type { LoadedAsset } from "./assetLoader.js";
  import type { CameraState } from "../types";
  import type { CameraSyncManager } from "./cameraSyncManager.js";

  interface Props {
    asset: LoadedAsset | null;
    label: string;
    height: number;
    syncManager: CameraSyncManager;
    initialCamera: CameraState | null;
    pointSize: number;
    loading: boolean;
    error: string | null;
  }

  let { asset, label, height, syncManager, initialCamera, pointSize, loading, error }: Props = $props();

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

    syncManager.register({ id: viewportId, camera: _camera, controls: _controls, render: renderFrame });

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
    cam.zoom = ic.zoom;
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
    const ps = pointSize;
    if (!a?.object3d) return;
    a.object3d.traverse((child) => {
      const pts = child as THREE.Points;
      if (pts.isPoints && pts.material) {
        (pts.material as THREE.PointsMaterial).size = ps * 0.01;
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
</script>

<div class="viewport-wrapper" style="height: {height}px; position: relative;">
  <div class="viewport-label">{label}</div>

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

  <canvas bind:this={canvasEl} style="width:100%; height:{height}px; display:block;"></canvas>
</div>

<style>
  .viewport-wrapper {
    position: relative;
    background: #1a1a2e;
    border-radius: 6px;
    overflow: hidden;
    flex: 1 1 0;
    min-width: 0;
  }
  .viewport-label {
    position: absolute;
    top: 8px;
    left: 8px;
    z-index: 10;
    background: rgba(0,0,0,0.55);
    color: #e0e0e0;
    font-size: 12px;
    font-family: monospace;
    padding: 3px 8px;
    border-radius: 4px;
    pointer-events: none;
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
    font-family: monospace;
    pointer-events: none;
  }
  .loading-overlay { background: rgba(26,26,46,0.85); color: #aaa; }
  .error-overlay   { background: rgba(80,20,20,0.85);  color: #ff8888; }
  .spinner {
    width: 28px; height: 28px;
    border: 3px solid #444;
    border-top-color: #7eb8f7;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
