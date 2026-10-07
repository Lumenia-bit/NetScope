import type { Device, DeviceEvent, NetworkInfo, ScanStatus, Settings } from "./types";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  devices: () => request<Device[]>("/api/devices"),
  device: (id: number) => request<Device>(`/api/devices/${id}`),
  history: (id: number) => request<DeviceEvent[]>(`/api/devices/${id}/history`),
  network: () => request<NetworkInfo>("/api/network"),
  scanStatus: () => request<ScanStatus>("/api/scan/status"),
  startScan: () => request<ScanStatus>("/api/scan", { method: "POST", body: "{}" }),
  scanPorts: (id: number) =>
    request<{ device: Device }>(`/api/devices/${id}/scan-ports`, {
      method: "POST",
      body: "{}",
    }),
  settings: () => request<Settings>("/api/settings"),
  updateSettings: (settings: Settings) =>
    request<Settings>("/api/settings", {
      method: "PUT",
      body: JSON.stringify(settings),
    }),
};

