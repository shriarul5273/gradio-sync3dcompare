import type { LoadingStatus } from "@gradio/utils";

export type AssetType = "ply" | "glb";
export type RenderMode = "points" | "native";

export interface AssetDescriptor {
  name?: string;
  path: string;
  url?: string;           // Gradio-served URL the browser can actually fetch
  type: AssetType;
  visible?: boolean;
  color?: [number, number, number];
  metadata?: Record<string, unknown>;
}

export interface Sync3DCompareValue {
  assets: AssetDescriptor[];
  render_mode: RenderMode;
  sync_camera: boolean;
  point_size: number;
  max_point_size: number;
  height: number;
  default_zoom: number;
  min_zoom: number;
  max_zoom: number;
}

export interface CameraState {
  position: { x: number; y: number; z: number };
  target: { x: number; y: number; z: number };
  zoom: number;
  up: { x: number; y: number; z: number };
}

export interface Sync3DCompareProps {
  value: Sync3DCompareValue | null;
  render_mode?: RenderMode;
  sync_camera?: boolean;
  point_size?: number;
  max_point_size?: number;
  height?: number;
  max_views?: number;
  default_zoom?: number;
  min_zoom?: number;
  max_zoom?: number;
}

export interface Sync3DCompareEvents {
  change: Sync3DCompareValue;
  clear_status: LoadingStatus;
}
