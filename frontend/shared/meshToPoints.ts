import * as THREE from "three";

const SAMPLE_COUNT = 100_000;

/**
 * Samples surface points from all meshes in a GLB scene.
 * Returns a Points object for display.
 */
export function glbToPoints(
  scene: THREE.Object3D,
  fallbackColor: [number, number, number] = [180, 180, 180],
  sampleCount: number = SAMPLE_COUNT
): THREE.Points {
  const positions: number[] = [];
  const colors: number[] = [];

  const meshes: THREE.Mesh[] = [];
  scene.traverse((child) => {
    if ((child as THREE.Mesh).isMesh) {
      meshes.push(child as THREE.Mesh);
    }
  });

  if (meshes.length === 0) {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute([], 3));
    return new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.02 }));
  }

  // Compute total triangle count for proportional sampling
  let totalArea = 0;
  const meshAreas: number[] = [];
  for (const mesh of meshes) {
    const area = estimateMeshArea(mesh);
    meshAreas.push(area);
    totalArea += area;
  }

  for (let m = 0; m < meshes.length; m++) {
    const mesh = meshes[m];
    const meshSamples =
      totalArea > 0
        ? Math.max(1, Math.round((meshAreas[m] / totalArea) * sampleCount))
        : Math.round(sampleCount / meshes.length);

    sampleMesh(mesh, meshSamples, positions, colors, fallbackColor);
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));

  const mat = new THREE.PointsMaterial({
    size: 0.02,
    vertexColors: true,
    sizeAttenuation: true,
  });

  return new THREE.Points(geo, mat);
}

function estimateMeshArea(mesh: THREE.Mesh): number {
  const geo = mesh.geometry;
  if (!geo) return 1;
  const pos = geo.attributes.position;
  if (!pos) return 1;

  let area = 0;
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const c = new THREE.Vector3();
  const cross = new THREE.Vector3();

  if (geo.index) {
    const idx = geo.index;
    for (let i = 0; i < idx.count; i += 3) {
      a.fromBufferAttribute(pos, idx.getX(i));
      b.fromBufferAttribute(pos, idx.getX(i + 1));
      c.fromBufferAttribute(pos, idx.getX(i + 2));
      cross.crossVectors(b.clone().sub(a), c.clone().sub(a));
      area += cross.length() * 0.5;
    }
  } else {
    for (let i = 0; i < pos.count; i += 3) {
      a.fromBufferAttribute(pos, i);
      b.fromBufferAttribute(pos, i + 1);
      c.fromBufferAttribute(pos, i + 2);
      cross.crossVectors(b.clone().sub(a), c.clone().sub(a));
      area += cross.length() * 0.5;
    }
  }
  return area || 1;
}

function sampleMesh(
  mesh: THREE.Mesh,
  count: number,
  outPositions: number[],
  outColors: number[],
  fallbackColor: [number, number, number]
): void {
  const geo = mesh.geometry;
  const pos = geo.attributes.position;
  if (!pos || pos.count === 0) return;

  const hasColor = !!geo.attributes.color;
  const colorAttr = geo.attributes.color;
  const mat = mesh.material as THREE.MeshStandardMaterial;
  const matColor = mat?.color ?? new THREE.Color(
    fallbackColor[0] / 255,
    fallbackColor[1] / 255,
    fallbackColor[2] / 255
  );

  const worldMatrix = mesh.matrixWorld;
  const tempA = new THREE.Vector3();
  const tempB = new THREE.Vector3();
  const tempC = new THREE.Vector3();
  const tempP = new THREE.Vector3();

  // Build triangle list
  const triangles: number[][] = [];
  if (geo.index) {
    const idx = geo.index;
    for (let i = 0; i < idx.count; i += 3) {
      triangles.push([idx.getX(i), idx.getX(i + 1), idx.getX(i + 2)]);
    }
  } else {
    for (let i = 0; i < pos.count; i += 3) {
      triangles.push([i, i + 1, i + 2]);
    }
  }

  if (triangles.length === 0) return;

  for (let s = 0; s < count; s++) {
    const triIdx = Math.floor(Math.random() * triangles.length);
    const [ia, ib, ic] = triangles[triIdx];

    tempA.fromBufferAttribute(pos, ia).applyMatrix4(worldMatrix);
    tempB.fromBufferAttribute(pos, ib).applyMatrix4(worldMatrix);
    tempC.fromBufferAttribute(pos, ic).applyMatrix4(worldMatrix);

    // Random barycentric point on triangle
    let r1 = Math.random();
    let r2 = Math.random();
    if (r1 + r2 > 1) { r1 = 1 - r1; r2 = 1 - r2; }
    const r3 = 1 - r1 - r2;

    tempP.set(
      r1 * tempA.x + r2 * tempB.x + r3 * tempC.x,
      r1 * tempA.y + r2 * tempB.y + r3 * tempC.y,
      r1 * tempA.z + r2 * tempB.z + r3 * tempC.z
    );

    outPositions.push(tempP.x, tempP.y, tempP.z);

    if (hasColor) {
      const ca = new THREE.Color().fromBufferAttribute(colorAttr as THREE.BufferAttribute, ia);
      const cb = new THREE.Color().fromBufferAttribute(colorAttr as THREE.BufferAttribute, ib);
      const cc = new THREE.Color().fromBufferAttribute(colorAttr as THREE.BufferAttribute, ic);
      outColors.push(
        r1 * ca.r + r2 * cb.r + r3 * cc.r,
        r1 * ca.g + r2 * cb.g + r3 * cc.g,
        r1 * ca.b + r2 * cb.b + r3 * cc.b
      );
    } else {
      outColors.push(matColor.r, matColor.g, matColor.b);
    }
  }
}
