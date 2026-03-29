<script lang="ts">
  import { onDestroy, untrack } from "svelte";
  import Viewport from "./Viewport.svelte";
  import { CameraSyncManager } from "./cameraSyncManager.js";
  import { loadAsset } from "./assetLoader.js";
  import {
    applyCameraZoom,
    computeAutoCamera,
    getCameraDistance,
    mergeBoxes,
  } from "./boundingBox.js";
  import type { LoadedAsset } from "./assetLoader.js";
  import type {
    AssetDescriptor,
    AssetType,
    Sync3DCompareValue,
    RenderMode,
    CameraState,
    PointSizeMode,
  } from "../types";

  const ACCEPTED_FILE_TYPES = ".ply,.glb,model/gltf-binary";
  const MIN_POINT_SIZE = 0.5;
  const CAMERA_FIELD_OF_VIEW = 60;

  interface Props {
    value: Sync3DCompareValue | null;
    render_mode?: RenderMode;
    sync_camera?: boolean;
    point_size_mode?: PointSizeMode;
    point_size?: number;
    max_point_size?: number;
    height?: number;
    max_views?: number;
    default_zoom?: number;
    min_zoom?: number;
    max_zoom?: number;
    onchange?: (value: Sync3DCompareValue) => void;
  }

  let {
    value,
    render_mode = "points",
    sync_camera = true,
    point_size_mode = "auto",
    point_size = 1.0,
    max_point_size = 10.0,
    height = 500,
    max_views = 4,
    default_zoom = 1.0,
    min_zoom = 0.5,
    max_zoom = 16.0,
    onchange,
  }: Props = $props();

  let fileInputEl: HTMLInputElement;
  let gridEl: HTMLDivElement | null = null;
  let uploadTarget = $state<{ slotIndex: number; sourceIndex: number | null } | null>(null);
  let managedObjectUrls = new Set<string>();
  let viewportAspect = $state(1);
  let pendingAutoFit = $state(false);

  function clampZoom(value: number, minValue: number, maxValue: number): number {
    return Math.min(Math.max(value, minValue), maxValue);
  }

  function clampPointSize(value: number, maxValue: number): number {
    const safeMaxValue = Math.max(maxValue, MIN_POINT_SIZE);
    return Math.min(Math.max(value, MIN_POINT_SIZE), safeMaxValue);
  }

  function cloneAsset(asset: AssetDescriptor): AssetDescriptor {
    return {
      ...asset,
      color: asset.color ? ([...asset.color] as [number, number, number]) : undefined,
      metadata: asset.metadata ? { ...asset.metadata } : undefined,
    };
  }

  function buildAssetReloadKey(asset: AssetDescriptor): string {
    return [
      asset.path,
      asset.url ?? "",
      asset.type,
      asset.color?.join(",") ?? "",
    ].join("|");
  }

  function syncManagedUrls(nextValue: Sync3DCompareValue | null): void {
    const nextUrls = new Set(
      (nextValue?.assets ?? [])
        .map((asset) => asset.url)
        .filter((url): url is string => typeof url === "string" && url.length > 0)
    );

    for (const objectUrl of Array.from(managedObjectUrls)) {
      if (!nextUrls.has(objectUrl)) {
        URL.revokeObjectURL(objectUrl);
        managedObjectUrls.delete(objectUrl);
      }
    }
  }

  function buildInitialValue(nextValue: Sync3DCompareValue | null): Sync3DCompareValue {
    const safeMinZoom = Math.max(nextValue?.min_zoom ?? min_zoom, 0.1);
    const safeMaxZoom = Math.max(nextValue?.max_zoom ?? max_zoom, safeMinZoom);
    const safeDefaultZoom = clampZoom(
      nextValue?.default_zoom ?? default_zoom,
      safeMinZoom,
      safeMaxZoom
    );
    const safeMaxPointSize = Math.max(nextValue?.max_point_size ?? max_point_size, MIN_POINT_SIZE);
    const safePointSize = clampPointSize(
      nextValue?.point_size ?? point_size,
      safeMaxPointSize
    );

    return {
      assets: (nextValue?.assets ?? []).map(cloneAsset),
      render_mode: nextValue?.render_mode ?? render_mode,
      sync_camera: nextValue?.sync_camera ?? sync_camera,
      point_size_mode: nextValue?.point_size_mode ?? point_size_mode,
      point_size: safePointSize,
      max_point_size: safeMaxPointSize,
      height: nextValue?.height ?? height,
      default_zoom: safeDefaultZoom,
      min_zoom: safeMinZoom,
      max_zoom: safeMaxZoom,
    };
  }

  function revokeManagedUrl(url?: string): void {
    if (!url || !managedObjectUrls.has(url)) return;
    URL.revokeObjectURL(url);
    managedObjectUrls.delete(url);
  }

  function revokeAllManagedUrls(): void {
    for (const objectUrl of managedObjectUrls) {
      URL.revokeObjectURL(objectUrl);
    }
    managedObjectUrls.clear();
  }

  function buildValue(
    nextAssets = assets,
    overrides: Partial<Sync3DCompareValue> = {}
  ): Sync3DCompareValue {
    const resolvedMaxPointSize = Math.max(
      overrides.max_point_size ?? maxPointSize,
      MIN_POINT_SIZE
    );
    return {
      assets: nextAssets.map(cloneAsset),
      render_mode: overrides.render_mode ?? currentRenderMode,
      sync_camera: overrides.sync_camera ?? syncCamera,
      point_size_mode: overrides.point_size_mode ?? currentPointSizeMode,
      point_size: clampPointSize(overrides.point_size ?? pointSize, resolvedMaxPointSize),
      max_point_size: resolvedMaxPointSize,
      height: overrides.height ?? viewerHeight,
      default_zoom: overrides.default_zoom ?? zoomLevel,
      min_zoom: overrides.min_zoom ?? minAllowedZoom,
      max_zoom: overrides.max_zoom ?? maxAllowedZoom,
    };
  }

  function commitValue(
    nextAssets = assets,
    overrides: Partial<Sync3DCompareValue> = {},
    emit = true
  ): Sync3DCompareValue {
    const nextValue = buildValue(nextAssets, overrides);
    runtimeValue = nextValue;
    if (emit) {
      onchange?.(nextValue);
    }
    return nextValue;
  }

  function inferAssetType(path: string): AssetType | null {
    const normalized = path.toLowerCase();
    if (normalized.endsWith(".ply")) return "ply";
    if (normalized.endsWith(".glb")) return "glb";
    return null;
  }

  function createLocalAsset(file: File): AssetDescriptor | null {
    const inferredType = inferAssetType(file.name);
    if (!inferredType) {
      return null;
    }

    const objectUrl = URL.createObjectURL(file);
    managedObjectUrls.add(objectUrl);

    return {
      name: file.name.replace(/\.[^/.]+$/, ""),
      path: file.name,
      url: objectUrl,
      type: inferredType,
      visible: true,
    };
  }

  function insertOrReplaceAsset(
    nextAssets: AssetDescriptor[],
    slotIndex: number,
    sourceIndex: number | null,
    asset: AssetDescriptor
  ): AssetDescriptor[] {
    const updatedAssets = [...nextAssets];

    if (sourceIndex !== null && updatedAssets[sourceIndex]) {
      revokeManagedUrl(updatedAssets[sourceIndex].url);
      updatedAssets[sourceIndex] = asset;
      return updatedAssets;
    }

    updatedAssets.splice(Math.min(slotIndex, updatedAssets.length), 0, asset);
    return updatedAssets;
  }

  async function loadUploadedFiles(
    files: File[],
    slotIndex: number,
    sourceIndex: number | null
  ): Promise<void> {
    const file = files[0];
    if (!file) return;

    const localAsset = createLocalAsset(file);
    if (!localAsset) {
      return;
    }

    const nextAssets = insertOrReplaceAsset(assets, slotIndex, sourceIndex, localAsset);
    commitValue(nextAssets);
  }

  let runtimeValue = $state(buildInitialValue(value));

  let assets = $derived(runtimeValue.assets ?? []);
  let syncCamera = $derived(runtimeValue.sync_camera);
  let viewerHeight = $derived(runtimeValue.height);
  let minAllowedZoom = $derived(runtimeValue.min_zoom);
  let maxAllowedZoom = $derived(runtimeValue.max_zoom);
  let maxViews = $derived(Math.max(2, max_views));
  let assetReloadKey = $derived(assets.map(buildAssetReloadKey).join("||"));
  let viewportItems = $derived(
    assets
      .map((asset, index) => ({ asset, index }))
      .filter(({ asset }) => asset.visible !== false)
  );
  let slotCount = $derived(Math.min(Math.max(viewportItems.length, 2), maxViews));
  let gridColumns = $derived(Math.min(slotCount, 2));
  let displaySlots = $derived(
    Array.from({ length: slotCount }, (_, slotIndex) => {
      const item = viewportItems[slotIndex];
      return {
        slotIndex,
        descriptor: item?.asset ?? null,
        sourceIndex: item?.index ?? null,
      };
    })
  );

  let pointSize = $state(runtimeValue.point_size);
  let maxPointSize = $state(runtimeValue.max_point_size);
  let currentPointSizeMode = $state<PointSizeMode>(runtimeValue.point_size_mode);
  let currentRenderMode = $state<RenderMode>(runtimeValue.render_mode);
  let zoomLevel = $state(runtimeValue.default_zoom);
  let appliedZoomLevel = $state(runtimeValue.default_zoom);

  let syncManager = new CameraSyncManager();
  let loadedAssets = $state<(LoadedAsset | null)[]>([]);
  let loadingStates = $state<boolean[]>([]);
  let errorStates = $state<(string | null)[]>([]);
  let initialCamera = $state<CameraState | null>(null);
  let fitReferenceCamera = $state<CameraState | null>(null);
  let loadRequestId = 0;

  onDestroy(() => {
    revokeAllManagedUrls();
  });

  function updateViewportAspect() {
    if (!gridEl) return;

    const firstViewport = gridEl.querySelector<HTMLElement>(".viewport-wrapper");
    const fallbackWidth = Math.max(gridEl.clientWidth, 1);
    const measuredWidth = firstViewport?.clientWidth ?? fallbackWidth;
    const nextAspect = measuredWidth / Math.max(viewerHeight, 1);

    if (Number.isFinite(nextAspect) && nextAspect > 0) {
      viewportAspect = nextAspect;
    }
  }

  function buildBaseFittedCamera(): CameraState | null {
    const boxes = loadedAssets
      .filter((loadedAsset) => loadedAsset !== null)
      .map((loadedAsset) => loadedAsset!.bounds);

    if (boxes.length === 0) {
      return null;
    }

    const globalBox = mergeBoxes(boxes);
    const dx = globalBox.max.x - globalBox.min.x;
    const dy = globalBox.max.y - globalBox.min.y;
    const dz = globalBox.max.z - globalBox.min.z;
    syncManager.setSceneDiameter(Math.sqrt(dx * dx + dy * dy + dz * dz));
    return computeAutoCamera(globalBox, viewportAspect, CAMERA_FIELD_OF_VIEW);
  }

  function updateZoomFromCameraState(state: CameraState): void {
    const referenceCamera = fitReferenceCamera;
    if (!referenceCamera) {
      return;
    }

    const baseDistance = Math.max(getCameraDistance(referenceCamera), 1e-6);
    const currentDistance = Math.max(getCameraDistance(state), 1e-6);
    const nextZoom = clampZoom(baseDistance / currentDistance, minAllowedZoom, maxAllowedZoom);

    zoomLevel = nextZoom;
    appliedZoomLevel = nextZoom;
  }

  $effect(() => {
    const nextValue = value;
    syncManagedUrls(nextValue);
    runtimeValue = buildInitialValue(nextValue);
  });

  $effect(() => {
    currentRenderMode = runtimeValue.render_mode;
  });

  $effect(() => {
    pointSize = runtimeValue.point_size;
  });

  $effect(() => {
    currentPointSizeMode = runtimeValue.point_size_mode;
  });

  $effect(() => {
    maxPointSize = Math.max(runtimeValue.max_point_size, MIN_POINT_SIZE);
    pointSize = clampPointSize(runtimeValue.point_size, maxPointSize);
  });

  $effect(() => {
    zoomLevel = clampZoom(runtimeValue.default_zoom, minAllowedZoom, maxAllowedZoom);
  });

  $effect(() => {
    syncManager.setEnabled(syncCamera);
  });

  $effect(() => {
    fitReferenceCamera;
    minAllowedZoom;
    maxAllowedZoom;

    syncManager.setStateChangeHandler((state) => {
      updateZoomFromCameraState(state);
    });

    return () => {
      syncManager.setStateChangeHandler(null);
    };
  });

  $effect(() => {
    gridEl;
    gridColumns;
    viewerHeight;
    displaySlots.length;
    queueMicrotask(() => updateViewportAspect());
  });

  $effect(() => {
    assetReloadKey;
    const mode = currentRenderMode;
    const currentAssets = untrack(() => assets);
    const initialPointSize = untrack(() => pointSize);
    if (currentAssets.length > 0) {
      loadAllAssets(currentAssets, mode, initialPointSize);
    } else {
      loadedAssets = [];
      loadingStates = [];
      errorStates = [];
      initialCamera = null;
      fitReferenceCamera = null;
      pendingAutoFit = false;
      zoomLevel = clampZoom(runtimeValue.default_zoom, minAllowedZoom, maxAllowedZoom);
      appliedZoomLevel = zoomLevel;
    }
  });

  $effect(() => {
    const shouldAutoFit = pendingAutoFit;
    const aspect = viewportAspect;
    if (!shouldAutoFit || aspect <= 0) return;

    updateViewportAspect();
    const baseFittedCamera = buildBaseFittedCamera();
    pendingAutoFit = false;
    if (!baseFittedCamera) {
      initialCamera = null;
      fitReferenceCamera = null;
      return;
    }

    const fittedZoom = clampZoom(runtimeValue.default_zoom, minAllowedZoom, maxAllowedZoom);
    const fittedCamera = applyCameraZoom(baseFittedCamera, fittedZoom);

    fitReferenceCamera = baseFittedCamera;
    initialCamera = fittedCamera;
    zoomLevel = fittedCamera.zoom;
    appliedZoomLevel = fittedCamera.zoom;
    syncManager.resetAll(fittedCamera);
  });

  async function loadAllAssets(
    currentAssets: AssetDescriptor[] = assets,
    mode: RenderMode = currentRenderMode,
    initialPointSize = pointSize
  ) {
    const requestId = ++loadRequestId;
    const assetCount = currentAssets.length;
    const nextLoadedAssets: (LoadedAsset | null)[] = new Array(assetCount).fill(null);
    const nextLoadingStates: boolean[] = new Array(assetCount).fill(true);
    const nextErrorStates: (string | null)[] = new Array(assetCount).fill(null);

    loadedAssets = nextLoadedAssets;
    loadingStates = nextLoadingStates;
    errorStates = nextErrorStates;

    await Promise.allSettled(
      currentAssets.map((asset, index) =>
        loadAsset(asset, mode, initialPointSize)
          .then((loadedAsset) => {
            nextLoadedAssets[index] = loadedAsset;
            nextLoadingStates[index] = false;
            return loadedAsset;
          })
          .catch((error) => {
            nextErrorStates[index] = `Failed to load: ${asset.path.split("/").pop()}`;
            nextLoadingStates[index] = false;
            throw error;
          })
      )
    );

    if (requestId !== loadRequestId) {
      return;
    }

    loadedAssets = nextLoadedAssets;
    loadingStates = nextLoadingStates;
    errorStates = nextErrorStates;
    initialCamera = null;
    pendingAutoFit = true;
  }

  function handleReset() {
    const baseFittedCamera = buildBaseFittedCamera();
    if (!baseFittedCamera) return;

    const fittedCamera = applyCameraZoom(
      baseFittedCamera,
      clampZoom(runtimeValue.default_zoom, minAllowedZoom, maxAllowedZoom)
    );
    fitReferenceCamera = baseFittedCamera;
    initialCamera = fittedCamera;
    zoomLevel = fittedCamera.zoom;
    appliedZoomLevel = fittedCamera.zoom;
    syncManager.resetAll(fittedCamera);
  }

  function handleRenderModeChange(mode: RenderMode) {
    currentRenderMode = mode;
    commitValue(assets, { render_mode: mode });
  }

  function handlePointSizeChange() {
    pointSize = clampPointSize(pointSize, maxPointSize);
    commitValue(assets, { point_size: pointSize });
  }

  function handlePointSizeModeChange(mode: PointSizeMode) {
    currentPointSizeMode = mode;
    commitValue(assets, { point_size_mode: mode });
  }

  function handleZoomChange() {
    const nextZoom = clampZoom(zoomLevel, minAllowedZoom, maxAllowedZoom);
    syncManager.setZoom(nextZoom, appliedZoomLevel);
    zoomLevel = nextZoom;
    appliedZoomLevel = nextZoom;
    commitValue(assets, { default_zoom: nextZoom }, false);
  }

  function handleUploadRequest(slotIndex: number, sourceIndex: number | null) {
    uploadTarget = { slotIndex, sourceIndex };
    fileInputEl?.click();
  }

  async function handleFileInputChange(event: Event) {
    const input = event.currentTarget as HTMLInputElement;
    const files = Array.from(input.files ?? []);
    if (!uploadTarget || files.length === 0) {
      input.value = "";
      return;
    }

    await loadUploadedFiles(files, uploadTarget.slotIndex, uploadTarget.sourceIndex);
    uploadTarget = null;
    input.value = "";
  }

  async function handleDroppedFiles(
    files: File[],
    slotIndex: number,
    sourceIndex: number | null
  ) {
    await loadUploadedFiles(files, slotIndex, sourceIndex);
  }

  function handleRemoveAsset(sourceIndex: number | null) {
    if (sourceIndex === null || !assets[sourceIndex]) {
      return;
    }

    revokeManagedUrl(assets[sourceIndex].url);
    const nextAssets = assets.filter((_, index) => index !== sourceIndex);
    commitValue(nextAssets);
  }
</script>

<div class="sync3d-root">
  <div class="toolbar">
    <div class="toolbar-cluster">
      <button class="toolbar-btn reset-btn" onclick={handleReset} title="Reset all cameras">
        <span class="reset-icon">⟳</span>
        <span>Reset</span>
      </button>

      <div class="toolbar-group">
        <span class="toolbar-label">Mode:</span>
        <div class="segmented-control">
          <button
            class="toolbar-btn mode-btn {currentRenderMode === 'points' ? 'active' : ''}"
            onclick={() => handleRenderModeChange("points")}
          >Points</button>
          <button
            class="toolbar-btn mode-btn {currentRenderMode === 'native' ? 'active' : ''}"
            onclick={() => handleRenderModeChange("native")}
          >Native</button>
        </div>
      </div>

      <div class="toolbar-group">
        <span class="toolbar-label">Point Size:</span>
        <div class="segmented-control">
          <button
            class="toolbar-btn mode-btn {currentPointSizeMode === 'auto' ? 'active' : ''}"
            onclick={() => handlePointSizeModeChange("auto")}
          >Auto</button>
          <button
            class="toolbar-btn mode-btn {currentPointSizeMode === 'manual' ? 'active' : ''}"
            onclick={() => handlePointSizeModeChange("manual")}
          >Manual</button>
        </div>
      </div>
    </div>

    <div class="toolbar-cluster controls-cluster">
      <div class="toolbar-group slider-group">
        <span class="toolbar-label">
          {currentPointSizeMode === "auto" ? "Size Multiplier" : "Size"}: {pointSize.toFixed(1)}
        </span>
        <input
          type="range"
          min={MIN_POINT_SIZE}
          max={maxPointSize}
          step={currentPointSizeMode === "auto" ? "0.1" : "0.5"}
          bind:value={pointSize}
          class="toolbar-slider"
          oninput={handlePointSizeChange}
        />
      </div>

      <div class="toolbar-group slider-group">
        <span class="toolbar-label">Zoom: {zoomLevel.toFixed(2)}x</span>
        <input
          type="range"
          min={minAllowedZoom}
          max={maxAllowedZoom}
          step="0.05"
          bind:value={zoomLevel}
          class="toolbar-slider"
          oninput={handleZoomChange}
        />
      </div>
    </div>
  </div>

  <div bind:this={gridEl} class="viewports-grid" style="--grid-columns: {gridColumns};">
    {#each displaySlots as slot (slot.slotIndex)}
      <Viewport
        asset={slot.sourceIndex === null ? null : loadedAssets[slot.sourceIndex] ?? null}
        label={slot.descriptor?.name ?? `View ${slot.slotIndex + 1}`}
        height={viewerHeight}
        {syncManager}
        {initialCamera}
        pointSizeMode={currentPointSizeMode}
        {pointSize}
        loading={slot.sourceIndex === null ? false : loadingStates[slot.sourceIndex] ?? true}
        error={slot.sourceIndex === null ? null : errorStates[slot.sourceIndex] ?? null}
        placeholder={slot.descriptor === null}
        uploadable={slot.descriptor === null}
        request_upload={() => handleUploadRequest(slot.slotIndex, slot.sourceIndex)}
        drop_files={(files) => handleDroppedFiles(files, slot.slotIndex, slot.sourceIndex)}
        removable={slot.sourceIndex !== null}
        remove_asset={() => handleRemoveAsset(slot.sourceIndex)}
      />
    {/each}
  </div>

  <input
    bind:this={fileInputEl}
    class="hidden-file-input"
    type="file"
    accept={ACCEPTED_FILE_TYPES}
    onchange={handleFileInputChange}
  />
</div>

<style>
  .sync3d-root {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 8px;
    background: linear-gradient(180deg, #111723 0%, #0d1320 100%);
    border: 1px solid #1f2b40;
    border-radius: 10px;
    font-family: ui-sans-serif, system-ui, sans-serif;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
  }

  .toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 8px 10px;
    background: #151d2c;
    border: 1px solid #212d42;
    border-radius: 8px;
    flex-wrap: wrap;
  }

  .toolbar-cluster {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .controls-cluster {
    margin-left: auto;
  }

  .toolbar-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .toolbar-label {
    font-size: 12px;
    color: #bdc8ef;
    white-space: nowrap;
    letter-spacing: 0.01em;
  }

  .toolbar-btn {
    background: #202b3f;
    color: #d7ddf7;
    border: 1px solid #31425f;
    border-radius: 7px;
    padding: 5px 10px;
    font-size: 12px;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }

  .toolbar-btn:hover {
    background: #26334a;
    border-color: #42557a;
  }

  .toolbar-btn.active {
    background: #2154d6;
    border-color: #3c68df;
    color: #fff;
  }

  .reset-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .reset-icon {
    font-size: 11px;
    line-height: 1;
  }

  .segmented-control {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px;
    background: #101827;
    border: 1px solid #243247;
    border-radius: 8px;
  }

  .mode-btn {
    min-width: 64px;
  }

  .slider-group {
    min-width: 0;
  }

  .toolbar-slider {
    width: 120px;
    accent-color: #7da2ff;
  }

  .viewports-grid {
    display: grid;
    grid-template-columns: repeat(var(--grid-columns), minmax(0, 1fr));
    gap: 8px;
  }

  .hidden-file-input {
    display: none;
  }

  @media (max-width: 720px) {
    .toolbar {
      justify-content: flex-start;
    }

    .controls-cluster {
      margin-left: 0;
    }

    .viewports-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
