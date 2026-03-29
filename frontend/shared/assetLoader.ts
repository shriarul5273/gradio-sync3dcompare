import * as THREE from "three";
import { PLYLoader } from "three/examples/jsm/loaders/PLYLoader.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { glbToPoints } from "./meshToPoints.js";
import { computeAutoPointSize, getPointCloudMetrics } from "./pointSizing.js";
import type { AssetDescriptor, RenderMode } from "../types";

export interface LoadedAsset {
  id: string;
  name: string;
  type: "ply" | "glb";
  object3d: THREE.Object3D;
  bounds: THREE.Box3;
  fitSphere: THREE.Sphere;
  basePointSize: number | null;
}

export async function loadAsset(
  asset: AssetDescriptor,
  renderMode: RenderMode,
  pointSize: number
): Promise<LoadedAsset> {
  const name = asset.name ?? asset.path.split("/").pop() ?? "Asset";
  const fallbackColor: [number, number, number] = asset.color
    ? [asset.color[0], asset.color[1], asset.color[2]]
    : [180, 180, 180];

  // Prefer the Gradio-served URL; fall back to raw path (for http URLs or tests)
  const fetchUrl = asset.url ?? asset.path;

  if (asset.type === "ply") {
    return loadPLY(fetchUrl, name, fallbackColor, pointSize);
  } else {
    return loadGLB(fetchUrl, name, renderMode, fallbackColor, pointSize);
  }
}

async function loadPLY(
  path: string,
  name: string,
  fallbackColor: [number, number, number],
  pointSize: number
): Promise<LoadedAsset> {
  const loader = new PLYLoader();
  const geometry: THREE.BufferGeometry = await new Promise((resolve, reject) => {
    loader.load(path, resolve, undefined, reject);
  });

  geometry.computeBoundingBox();

  const hasColor = !!geometry.attributes.color;
  const material = new THREE.PointsMaterial({
    size: pointSize * 0.01,
    vertexColors: hasColor,
    color: hasColor
      ? undefined
      : new THREE.Color(
          fallbackColor[0] / 255,
          fallbackColor[1] / 255,
          fallbackColor[2] / 255
        ),
    sizeAttenuation: true,
  });

  const points = new THREE.Points(geometry, material);
  points.frustumCulled = false;
  const bounds = new THREE.Box3().setFromObject(points);
  const fitSphere = bounds.getBoundingSphere(new THREE.Sphere());
  const basePointSize = computeAutoPointSize(bounds, geometry.attributes.position.count);

  return {
    id: crypto.randomUUID(),
    name,
    type: "ply",
    object3d: points,
    bounds,
    fitSphere,
    basePointSize,
  };
}

async function loadGLB(
  path: string,
  name: string,
  renderMode: RenderMode,
  fallbackColor: [number, number, number],
  pointSize: number
): Promise<LoadedAsset> {
  const loader = new GLTFLoader();
  const gltf = await new Promise<any>((resolve, reject) => {
    loader.load(path, resolve, undefined, reject);
  });

  const scene: THREE.Object3D = gltf.scene;

  // Ensure world matrices are up to date for sampling
  scene.updateMatrixWorld(true);

  let object3d: THREE.Object3D;
  let basePointSize: number | null = null;

  if (renderMode === "native") {
    object3d = scene;
    // Disable frustum culling on all meshes so parts never disappear during zoom
    scene.traverse((child) => {
      child.frustumCulled = false;
    });
    const pointMetrics = getPointCloudMetrics(scene);
    if (pointMetrics) {
      basePointSize = computeAutoPointSize(pointMetrics.bounds, pointMetrics.pointCount);
    }
  } else {
    // Convert to points
    const pts = glbToPoints(scene, fallbackColor);
    object3d = pts;
    const pointCount = pts.geometry.attributes.position?.count ?? 0;
    basePointSize =
      pointCount > 0 ? computeAutoPointSize(new THREE.Box3().setFromObject(pts), pointCount) : null;
  }

  const bounds = new THREE.Box3().setFromObject(object3d);
  const fitSphere = bounds.getBoundingSphere(new THREE.Sphere());

  return {
    id: crypto.randomUUID(),
    name,
    type: "glb",
    object3d,
    bounds,
    fitSphere,
    basePointSize,
  };
}
