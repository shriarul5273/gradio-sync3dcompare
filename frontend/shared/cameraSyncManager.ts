import type * as THREE from "three";
import type { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { CameraState } from "../types";

export interface ViewportEntry {
  id: string;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  render: () => void;
}

export class CameraSyncManager {
  private viewports = new Map<string, ViewportEntry>();
  private listeners = new Map<string, () => void>();
  private isSyncing = false;
  private syncEnabled = true;

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

  setZoom(zoom: number): void {
    for (const vp of this.viewports.values()) {
      vp.camera.zoom = zoom;
      vp.camera.updateProjectionMatrix();
      vp.controls.update();
      vp.render();
    }
  }

  resetAll(state: CameraState): void {
    for (const vp of this.viewports.values()) {
      this.applyState(vp, state);
      vp.controls.update();
      vp.render();
    }
  }

  private onControlChange(sourceId: string): void {
    if (this.isSyncing || !this.syncEnabled) return;

    this.isSyncing = true;
    try {
      const source = this.viewports.get(sourceId);
      if (!source) return;

      const state = this.extractState(source);

      for (const [id, vp] of this.viewports) {
        if (id === sourceId) continue;
        this.applyState(vp, state);
        vp.controls.update();
        vp.render();
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
      zoom: vp.camera.zoom,
      up: { x: up.x, y: up.y, z: up.z },
    };
  }

  private applyState(vp: ViewportEntry, state: CameraState): void {
    vp.camera.position.set(state.position.x, state.position.y, state.position.z);
    vp.camera.up.set(state.up.x, state.up.y, state.up.z);
    vp.camera.zoom = state.zoom;
    vp.camera.updateProjectionMatrix();
    vp.controls.target.set(state.target.x, state.target.y, state.target.z);
  }
}
