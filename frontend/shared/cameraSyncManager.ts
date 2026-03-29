import type * as THREE from "three";
import type { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { CameraState } from "../types";

export interface ViewportEntry {
  id: string;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  render: () => void;
}

const MIN_NEAR = 0.0001;

export class CameraSyncManager {
  private viewports = new Map<string, ViewportEntry>();
  private listeners = new Map<string, () => void>();
  private isSyncing = false;
  private syncEnabled = true;
  private stateChangeHandler: ((state: CameraState) => void) | null = null;
  private sceneDiameter = 1;

  setSceneDiameter(d: number): void {
    this.sceneDiameter = Math.max(d, 0.001);
  }

  private computeNearFar(distance: number): { near: number; far: number } {
    const safeDistance = Math.max(distance, MIN_NEAR);
    const near = Math.max(MIN_NEAR, safeDistance * 0.001);
    const far = Math.max(near * 100000, this.sceneDiameter * 10);
    return { near, far };
  }

  register(entry: ViewportEntry): void {
    const previous = this.viewports.get(entry.id);
    const previousListener = this.listeners.get(entry.id);
    if (previous && previousListener) {
      previous.controls.removeEventListener("change", previousListener);
    }

    this.viewports.set(entry.id, entry);
    const listener = () => {
      this.onControlChange(entry.id);
    };
    this.listeners.set(entry.id, listener);
    entry.controls.addEventListener("change", listener);
  }

  unregister(id: string): void {
    const entry = this.viewports.get(id);
    const listener = this.listeners.get(id);
    if (entry && listener) {
      entry.controls.removeEventListener("change", listener);
    }
    this.viewports.delete(id);
    this.listeners.delete(id);
  }

  setEnabled(enabled: boolean): void {
    this.syncEnabled = enabled;
  }

  setStateChangeHandler(handler: ((state: CameraState) => void) | null): void {
    this.stateChangeHandler = handler;
  }

  setZoom(nextZoom: number, previousZoom: number): void {
    const safePreviousZoom = Math.max(previousZoom, 0.1);
    const safeNextZoom = Math.max(nextZoom, 0.1);
    const distanceScale = safePreviousZoom / safeNextZoom;

    this.isSyncing = true;
    try {
      for (const vp of this.viewports.values()) {
        const offset = vp.camera.position.clone().sub(vp.controls.target);
        if (offset.lengthSq() === 0) {
          offset.set(0, 0, 1);
        }
        offset.multiplyScalar(distanceScale);
        vp.camera.position.copy(vp.controls.target).add(offset);
        vp.camera.zoom = 1;
        const { near, far } = this.computeNearFar(offset.length());
        vp.camera.near = near;
        vp.camera.far = far;
        vp.camera.updateProjectionMatrix();
        vp.controls.update();
        vp.render();
      }
    } finally {
      this.isSyncing = false;
    }

    const firstViewport = this.viewports.values().next().value;
    if (firstViewport && this.stateChangeHandler) {
      this.stateChangeHandler(this.extractState(firstViewport));
    }
  }

  resetAll(state: CameraState): void {
    for (const vp of this.viewports.values()) {
      this.applyState(vp, state);
      vp.controls.update();
      vp.render();
    }
    if (this.stateChangeHandler) {
      this.stateChangeHandler(state);
    }
  }

  private onControlChange(sourceId: string): void {
    if (this.isSyncing || !this.syncEnabled) return;

    this.isSyncing = true;
    try {
      const source = this.viewports.get(sourceId);
      if (!source) return;

      // Dynamically update near/far based on current camera-to-target distance
      const distance = source.camera.position.distanceTo(source.controls.target);
      if (distance > 0) {
        const { near, far } = this.computeNearFar(distance);
        source.camera.near = near;
        source.camera.far = far;
        source.camera.updateProjectionMatrix();
      }

      const state = this.extractState(source);

      for (const [id, vp] of this.viewports) {
        if (id === sourceId) continue;
        this.applyState(vp, state);
        vp.controls.update();
        vp.render();
      }

      if (this.stateChangeHandler) {
        this.stateChangeHandler(state);
      }
    } finally {
      this.isSyncing = false;
    }
  }

  private extractState(vp: ViewportEntry): CameraState {
    const pos = vp.camera.position;
    const target = vp.controls.target;
    const up = vp.camera.up;
    return {
      position: { x: pos.x, y: pos.y, z: pos.z },
      target: { x: target.x, y: target.y, z: target.z },
      zoom: 1,
      up: { x: up.x, y: up.y, z: up.z },
      near: vp.camera.near,
      far: vp.camera.far,
    };
  }

  private applyState(vp: ViewportEntry, state: CameraState): void {
    vp.camera.position.set(state.position.x, state.position.y, state.position.z);
    vp.camera.up.set(state.up.x, state.up.y, state.up.z);
    vp.camera.zoom = 1;
    if (state.near !== undefined) {
      vp.camera.near = state.near;
    }
    if (state.far !== undefined) {
      vp.camera.far = state.far;
    }
    vp.camera.updateProjectionMatrix();
    vp.controls.target.set(state.target.x, state.target.y, state.target.z);
  }
}
