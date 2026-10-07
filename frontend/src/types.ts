export interface Device {
  id: number;
  mac: string;
  ip: string;
  hostname: string | null;
  vendor: string;
  status: "online" | "offline";
  first_seen: string;
  last_seen: string;
  is_new: boolean;
  ports: number[];
  open_ports?: OpenPort[];
}

export interface OpenPort {
  port: number;
  service: string;
  state: "open";
}

export interface DeviceEvent {
  id: number;
  event: string;
  detail: string;
  occurred_at: string;
}

export interface ScanStatus {
  status: "idle" | "scanning" | "failed";
  progress: number;
  devices_discovered: number;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
}

export interface NetworkInfo {
  detected: {
    interface: string;
    address: string;
    subnet: string;
    gateway: string | null;
  } | null;
  configured_subnet: string | null;
  effective_subnet: string | null;
  detection_error: string | null;
}

export interface Settings {
  subnet: string | null;
  ports: number[];
  scan_timeout: number;
  resolve_hostnames: boolean;
  vendor_lookup: boolean;
}

