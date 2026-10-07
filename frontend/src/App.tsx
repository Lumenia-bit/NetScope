import { useCallback, useEffect, useState } from "react";
import { Activity, Radar, Settings as SettingsIcon } from "lucide-react";
import { api } from "./api";
import Dashboard from "./Dashboard";
import DevicePage from "./DevicePage";
import SettingsPage from "./SettingsPage";
import type { Device, NetworkInfo, ScanStatus } from "./types";

type Route = { page: "dashboard" } | { page: "settings" } | { page: "device"; id: number };

function readRoute(): Route {
  const deviceMatch = window.location.pathname.match(/^\/devices\/(\d+)$/);
  if (deviceMatch) return { page: "device", id: Number(deviceMatch[1]) };
  if (window.location.pathname === "/settings") return { page: "settings" };
  return { page: "dashboard" };
}

function App() {
  const [route, setRoute] = useState<Route>(readRoute);
  const [devices, setDevices] = useState<Device[]>([]);
  const [network, setNetwork] = useState<NetworkInfo | null>(null);
  const [scan, setScan] = useState<ScanStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const navigate = useCallback((path: string) => {
    window.history.pushState({}, "", path);
    setRoute(readRoute());
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [nextDevices, nextNetwork, nextScan] = await Promise.all([
        api.devices(),
        api.network(),
        api.scanStatus(),
      ]);
      setDevices(nextDevices);
      setNetwork(nextNetwork);
      setScan(nextScan);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reach NetScope");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const onPopState = () => setRoute(readRoute());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, [refresh]);

  useEffect(() => {
    if (scan?.status !== "scanning") return;
    const poll = window.setInterval(async () => {
      const nextScan = await api.scanStatus().catch(() => null);
      if (!nextScan) return;
      setScan(nextScan);
      if (nextScan.status !== "scanning") void refresh();
    }, 1000);
    return () => window.clearInterval(poll);
  }, [scan?.status, refresh]);

  const startScan = async () => {
    try {
      setError(null);
      setScan(await api.startScan());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start scan");
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => navigate("/")}>
          <span className="brand-mark"><Radar size={19} /></span>
          <span>NetScope</span>
        </button>
        <div className="network-label">
          <Activity size={14} />
          <span>Network</span>
          <strong>{network?.effective_subnet ?? "Not detected"}</strong>
        </div>
        <nav className="topnav" aria-label="Main navigation">
          <button className={route.page === "settings" ? "nav-button active" : "nav-button"} onClick={() => navigate("/settings")}>
            <SettingsIcon size={16} /> Settings
          </button>
          <button className="primary-button scan-button" onClick={startScan} disabled={scan?.status === "scanning"}>
            <Radar size={16} className={scan?.status === "scanning" ? "spin" : ""} />
            {scan?.status === "scanning" ? "Scanning…" : "Scan Network"}
          </button>
        </nav>
      </header>

      {scan?.status === "scanning" && (
        <div className="scan-progress" role="status">
          <div className="scan-progress-fill" style={{ width: `${scan.progress}%` }} />
          <span>Scanning network · {scan.progress}% · {scan.devices_discovered} found</span>
        </div>
      )}

      <main className="main-content">
        {error && <div className="notice error-notice">{error}</div>}
        {scan?.status === "failed" && scan.error && <div className="notice error-notice">Last scan failed: {scan.error}</div>}
        {route.page === "dashboard" && (
          <Dashboard devices={devices} loading={loading} onNavigate={navigate} />
        )}
        {route.page === "device" && <DevicePage id={route.id} onBack={() => navigate("/")} />}
        {route.page === "settings" && (
          <SettingsPage onSaved={() => { void refresh(); navigate("/"); }} />
        )}
      </main>
    </div>
  );
}

export default App;

