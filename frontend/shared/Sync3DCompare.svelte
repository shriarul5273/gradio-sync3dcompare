<script lang="ts">
  import { onMount } from "svelte";
  import * as THREE from "three";
  import Viewport from "./Viewport.svelte";
  import { CameraSyncManager } from "./cameraSyncManager.js";
  import { loadAsset } from "./assetLoader.js";
  import { computeAutoCamera, mergeBoxes } from "./boundingBox.js";
  import type { LoadedAsset } from "./assetLoader.js";
  import type { Sync3DCompareValue, RenderMode, CameraState } from "../types";

  interface Props {
    value: Sync3DCompareValue | null;
    onchange?: (value: Sync3DCompareValue) => void;
  }

  let { value, onchange }: Props = $props();

  // Derived config from value
  let assets = $derived(value?.assets ?? []);
  let renderMode = $derived<RenderMode>(value?.render_mode ?? "points");
  let syncCamera = $derived(value?.sync_camera ?? true);
  let height = $derived(value?.height ?? 500);

  let pointSize = $state(value?.point_size ?? 2.0);
  let currentRenderMode = $state<RenderMode>(value?.render_mode ?? "points");

  let syncManager = new CameraSyncManager();
  let loadedAssets = $state<(LoadedAsset | null)[]>([]);
  let loadingStates = $state<boolean[]>([]);
  let errorStates = $state<(string | null)[]>([]);
  let initialCamera = $state<CameraState | null>(null);
  let loaded = $state(false);

  $effect(() => {
    syncManager.setEnabled(syncCamera);
  });

  $effect(() => {
    if (assets.length > 0) {
      loadAllAssets();
    }
  });

  async function loadAllAssets() {
    const n = assets.length;
    loadedAssets = new Array(n).fill(null);
    loadingStates = new Array(n).fill(true);
    errorStates = new Array(n).fill(null);
    loaded = false;

    const results = await Promise.allSettled(
      assets.map((asset, i) =>
        loadAsset(asset, currentRenderMode, pointSize).then((la) => {
          loadedAssets[i] = la;
          loadingStates[i] = false;
          return la;
        }).catch((err) => {
          errorStates[i] = `Failed to load: ${asset.path.split("/").pop()}`;
          loadingStates[i] = false;
          throw err;
        })
      )
    );

    // Compute shared bounding box and initial camera
    const boxes: THREE.Box3[] = loadedAssets
      .filter((la) => la !== null)
      .map((la) => la!.bounds);

    if (boxes.length > 0) {
      const globalBox = mergeBoxes(boxes);
      initialCamera = computeAutoCamera(globalBox);
      syncManager.resetAll(initialCamera);
    }

    loaded = true;
  }

  function handleReset() {
    if (initialCamera) {
      syncManager.resetAll(initialCamera);
    }
  }

  async function handleRenderModeChange(mode: RenderMode) {
    currentRenderMode = mode;
    await loadAllAssets();
  }
</script>

<div class="sync3d-root">
  <!-- Toolbar -->
  <div class="toolbar">
    <button class="toolbar-btn" onclick={handleReset} title="Reset all cameras">
      ⟳ Reset
    </button>

    <div class="toolbar-group">
      <span class="toolbar-label">Mode:</span>
      <button
        class="toolbar-btn {currentRenderMode === 'points' ? 'active' : ''}"
        onclick={() => handleRenderModeChange('points')}
      >Points</button>
      <button
        class="toolbar-btn {currentRenderMode === 'native' ? 'active' : ''}"
        onclick={() => handleRenderModeChange('native')}
      >Native</button>
    </div>

    <div class="toolbar-group">
      <span class="toolbar-label">Point size: {pointSize.toFixed(1)}</span>
      <input
        type="range"
        min="0.5"
        max="10"
        step="0.5"
        bind:value={pointSize}
        class="point-slider"
      />
    </div>
  </div>

  <!-- Viewports -->
  <div class="viewports-row" style="height: {height}px;">
    {#each assets as asset, i}
      {#if asset.visible !== false}
        <Viewport
          asset={loadedAssets[i] ?? null}
          label={asset.name ?? `Asset ${i + 1}`}
          {height}
          {syncManager}
          {initialCamera}
          {pointSize}
          loading={loadingStates[i] ?? true}
          error={errorStates[i] ?? null}
        />
      {/if}
    {/each}

    {#if assets.length === 0}
      <div class="empty-state">No assets loaded. Provide a value with asset descriptors.</div>
    {/if}
  </div>
</div>

<style>
  .sync3d-root {
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-family: system-ui, sans-serif;
  }

  .toolbar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 10px;
    background: #111827;
    border-radius: 6px;
    flex-wrap: wrap;
  }

  .toolbar-group {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .toolbar-label {
    font-size: 12px;
    color: #9ca3af;
    white-space: nowrap;
  }

  .toolbar-btn {
    background: #1f2937;
    color: #d1d5db;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
    cursor: pointer;
    transition: background 0.15s;
  }

  .toolbar-btn:hover {
    background: #374151;
  }

  .toolbar-btn.active {
    background: #2563eb;
    border-color: #3b82f6;
    color: #fff;
  }

  .point-slider {
    width: 100px;
    accent-color: #3b82f6;
  }

  .viewports-row {
    display: flex;
    gap: 6px;
    overflow: hidden;
  }

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    color: #6b7280;
    font-size: 13px;
    border: 1px dashed #374151;
    border-radius: 6px;
    padding: 40px;
  }
</style>
