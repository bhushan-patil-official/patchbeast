/**
 * EDITORIAL hardware tier catalogue for the "can my PC run it" checker.
 * `score` is a coarse relative-performance tier (higher = faster), maintained by hand.
 * It is NOT benchmark data. The checker always shows this caveat.
 * Requirement rows reference these ids through `cpu_ref` / `gpu_ref` (set in the admin).
 */
export interface HardwareItem {
  id: string;
  name: string;
  kind: "cpu" | "gpu";
  score: number;
}

export const CPUS: HardwareItem[] = [
  { id: "amd-ryzen-5-1600", name: "AMD Ryzen 5 1600", kind: "cpu", score: 85 },
  { id: "intel-i5-8400", name: "Intel Core i5-8400", kind: "cpu", score: 100 },
  { id: "amd-ryzen-5-3600", name: "AMD Ryzen 5 3600", kind: "cpu", score: 125 },
  { id: "intel-i7-9700k", name: "Intel Core i7-9700K", kind: "cpu", score: 130 },
  { id: "intel-i5-12400f", name: "Intel Core i5-12400F", kind: "cpu", score: 160 },
  { id: "amd-ryzen-5-5600", name: "AMD Ryzen 5 5600", kind: "cpu", score: 165 },
  { id: "amd-ryzen-7-5800x3d", name: "AMD Ryzen 7 5800X3D", kind: "cpu", score: 215 },
  { id: "amd-ryzen-5-7600", name: "AMD Ryzen 5 7600", kind: "cpu", score: 215 },
  { id: "intel-i5-13600k", name: "Intel Core i5-13600K", kind: "cpu", score: 235 },
  { id: "amd-ryzen-7-7800x3d", name: "AMD Ryzen 7 7800X3D", kind: "cpu", score: 270 },
  { id: "intel-i9-13900k", name: "Intel Core i9-13900K", kind: "cpu", score: 290 },
];

export const GPUS: HardwareItem[] = [
  { id: "nvidia-gtx-1050-ti", name: "NVIDIA GeForce GTX 1050 Ti", kind: "gpu", score: 60 },
  { id: "nvidia-gtx-1060-6gb", name: "NVIDIA GeForce GTX 1060 6GB", kind: "gpu", score: 100 },
  { id: "amd-rx-580-8gb", name: "AMD Radeon RX 580 8GB", kind: "gpu", score: 105 },
  { id: "nvidia-gtx-1660-super", name: "NVIDIA GeForce GTX 1660 Super", kind: "gpu", score: 150 },
  { id: "nvidia-rtx-2060", name: "NVIDIA GeForce RTX 2060", kind: "gpu", score: 175 },
  { id: "nvidia-rtx-3060", name: "NVIDIA GeForce RTX 3060", kind: "gpu", score: 190 },
  { id: "amd-rx-6600-xt", name: "AMD Radeon RX 6600 XT", kind: "gpu", score: 215 },
  { id: "nvidia-rtx-4060", name: "NVIDIA GeForce RTX 4060", kind: "gpu", score: 220 },
  { id: "nvidia-rtx-3060-ti", name: "NVIDIA GeForce RTX 3060 Ti", kind: "gpu", score: 245 },
  { id: "nvidia-rtx-4060-ti", name: "NVIDIA GeForce RTX 4060 Ti", kind: "gpu", score: 265 },
  { id: "amd-rx-6700-xt", name: "AMD Radeon RX 6700 XT", kind: "gpu", score: 270 },
  { id: "nvidia-rtx-3070", name: "NVIDIA GeForce RTX 3070", kind: "gpu", score: 280 },
  { id: "nvidia-rtx-4070", name: "NVIDIA GeForce RTX 4070", kind: "gpu", score: 340 },
  { id: "amd-rx-7800-xt", name: "AMD Radeon RX 7800 XT", kind: "gpu", score: 400 },
  { id: "nvidia-rtx-4080", name: "NVIDIA GeForce RTX 4080", kind: "gpu", score: 560 },
  { id: "nvidia-rtx-4090", name: "NVIDIA GeForce RTX 4090", kind: "gpu", score: 750 },
];

export const RAM_OPTIONS = [4, 8, 12, 16, 24, 32, 48, 64];

export const byId = (list: HardwareItem[], id?: string) => list.find((i) => i.id === id);
