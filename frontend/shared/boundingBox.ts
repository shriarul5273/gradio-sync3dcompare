import * as THREE from "three";
import type { CameraState } from "../types";

const DEFAULT_CAMERA_DIRECTION = new THREE.Vector3(0, 0, 1);
const MIN_CAMERA_NEAR = 0.01;
const CAMERA_PADDING = 1.05;

function getBoxCorners(box: THREE.Box3): THREE.Vector3[] {
  const { min, max } = box;
  return [
    new THREE.Vector3(min.x, min.y, min.z),
    new THREE.Vector3(min.x, min.y, max.z),
    new THREE.Vector3(min.x, max.y, min.z),
    new THREE.Vector3(min.x, max.y, max.z),
    new THREE.Vector3(max.x, min.y, min.z),
    new THREE.Vector3(max.x, min.y, max.z),
    new THREE.Vector3(max.x, max.y, min.z),
    new THREE.Vector3(max.x, max.y, max.z),
  ];
}

export function computeAutoCamera(
  globalBox: THREE.Box3,
  aspectRatio: number,
  fieldOfViewDegrees: number
): CameraState {
  const center = new THREE.Vector3();
  globalBox.getCenter(center);
  const direction = DEFAULT_CAMERA_DIRECTION.clone().normalize();

  const worldUp = Math.abs(direction.y) > 0.98
    ? new THREE.Vector3(0, 0, 1)
    : new THREE.Vector3(0, 1, 0);
  const right = new THREE.Vector3().crossVectors(worldUp, direction).normalize();
  const up = new THREE.Vector3().crossVectors(direction, right).normalize();

  const verticalHalfFov = THREE.MathUtils.degToRad(fieldOfViewDegrees) / 2;
  const horizontalHalfFov =
    Math.atan(Math.tan(verticalHalfFov) * Math.max(aspectRatio, 0.1));
  const tanVertical = Math.max(Math.tan(verticalHalfFov), 1e-3);
  const tanHorizontal = Math.max(Math.tan(horizontalHalfFov), 1e-3);

  let requiredDistance = 1;
  let maxFrontDepth = 0;
  let maxBackDepth = 0;

  for (const corner of getBoxCorners(globalBox)) {
    const offset = corner.clone().sub(center);
    const horizontal = Math.abs(offset.dot(right));
    const vertical = Math.abs(offset.dot(up));
    const depth = offset.dot(direction);

    requiredDistance = Math.max(
      requiredDistance,
      depth + horizontal / tanHorizontal,
      depth + vertical / tanVertical
    );
    maxFrontDepth = Math.max(maxFrontDepth, depth);
    maxBackDepth = Math.max(maxBackDepth, -depth);
  }

  const distance = requiredDistance * CAMERA_PADDING;
  const position = center.clone().addScaledVector(direction, distance);
  const near = Math.max(MIN_CAMERA_NEAR, (distance - maxFrontDepth) * 0.5);
  const far = Math.max((distance + maxBackDepth) * 1.5, near + 1);

  return {
    position: {
      x: position.x,
      y: position.y,
      z: position.z,
    },
    target: { x: center.x, y: center.y, z: center.z },
    zoom: 1,
    up: { x: 0, y: 1, z: 0 },
    near,
    far,
  };
}

export function applyCameraZoom(
  baseState: CameraState,
  zoomFactor: number
): CameraState {
  const safeZoom = Math.max(zoomFactor, 0.1);
  const target = new THREE.Vector3(
    baseState.target.x,
    baseState.target.y,
    baseState.target.z
  );
  const position = new THREE.Vector3(
    baseState.position.x,
    baseState.position.y,
    baseState.position.z
  );
  const offset = position.sub(target);
  const scaledPosition = target.clone().add(offset.multiplyScalar(1 / safeZoom));

  return {
    ...baseState,
    position: {
      x: scaledPosition.x,
      y: scaledPosition.y,
      z: scaledPosition.z,
    },
    zoom: safeZoom,
    near:
      baseState.near !== undefined
        ? Math.max(MIN_CAMERA_NEAR, baseState.near / Math.max(safeZoom, 1))
        : baseState.near,
    far:
      baseState.far !== undefined
        ? baseState.far / Math.min(safeZoom, 1)
        : baseState.far,
  };
}

export function getCameraDistance(state: CameraState): number {
  const target = new THREE.Vector3(
    state.target.x,
    state.target.y,
    state.target.z
  );
  const position = new THREE.Vector3(
    state.position.x,
    state.position.y,
    state.position.z
  );
  return position.distanceTo(target);
}

export function mergeBoxes(boxes: THREE.Box3[]): THREE.Box3 {
  const merged = new THREE.Box3();
  for (const b of boxes) {
    merged.union(b);
  }
  return merged;
}
