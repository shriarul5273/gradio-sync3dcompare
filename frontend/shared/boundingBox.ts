import * as THREE from "three";
import type { CameraState } from "../types";

export function computeAutoCamera(globalBox: THREE.Box3): CameraState {
  const center = new THREE.Vector3();
  const size = new THREE.Vector3();
  globalBox.getCenter(center);
  globalBox.getSize(size);

  const maxDim = Math.max(size.x, size.y, size.z) || 1;
  const distance = maxDim * 2.5;

  return {
    position: {
      x: center.x + distance * 0.5,
      y: center.y + distance * 0.5,
      z: center.z + distance,
    },
    target: { x: center.x, y: center.y, z: center.z },
    zoom: 1,
    up: { x: 0, y: 1, z: 0 },
  };
}

export function mergeBoxes(boxes: THREE.Box3[]): THREE.Box3 {
  const merged = new THREE.Box3();
  for (const b of boxes) {
    merged.union(b);
  }
  return merged;
}
