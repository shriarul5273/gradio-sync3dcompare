import * as THREE from "three";
import type { PointSizeMode } from "../types";

const MANUAL_POINT_SIZE_SCALE = 0.01;
const AUTO_POINT_SIZE_FACTOR = 2;
const EPSILON = 1e-6;

export interface PointCloudMetrics {
  pointCount: number;
  bounds: THREE.Box3;
  sphere: THREE.Sphere;
}

export function getPointCloudMetrics(object3d: THREE.Object3D): PointCloudMetrics | null {
  let pointCount = 0;
  object3d.traverse((child) => {
    const points = child as THREE.Points;
    if (!points.isPoints) return;

    const position = points.geometry?.attributes?.position;
    if (!position) return;
    pointCount += position.count;
  });

  if (pointCount === 0) {
    return null;
  }

  const bounds = new THREE.Box3().setFromObject(object3d);
  const sphere = bounds.getBoundingSphere(new THREE.Sphere());

  return { pointCount, bounds, sphere };
}

export function computeAutoPointSize(
  bounds: THREE.Box3,
  pointCount: number
): number {
  const size = new THREE.Vector3();
  bounds.getSize(size);

  const spanX = Math.max(size.x, EPSILON);
  const spanY = Math.max(size.y, EPSILON);
  const spanZ = Math.max(size.z, EPSILON);
  const maxSpan = Math.max(spanX, spanY, spanZ);
  const dominantArea = Math.max(spanX * spanY, spanX * spanZ, spanY * spanZ, EPSILON);
  const estimatedSpacing = Math.sqrt(dominantArea / Math.max(pointCount, 1));

  return THREE.MathUtils.clamp(
    estimatedSpacing * AUTO_POINT_SIZE_FACTOR,
    maxSpan * 0.0002,
    maxSpan * 0.03
  );
}

export function resolvePointSize(
  mode: PointSizeMode,
  sliderValue: number,
  basePointSize: number | null
): number | null {
  if (mode === "manual") {
    return sliderValue * MANUAL_POINT_SIZE_SCALE;
  }

  if (basePointSize !== null) {
    return basePointSize * sliderValue;
  }

  return null;
}
