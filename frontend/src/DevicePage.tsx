import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Clock3, Cpu, Globe2, Network, Radar } from "lucide-react";
import { api } from "./api";
import type { Device, DeviceEvent } from "./types";

function exactTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "medium" }).format(new Date(value));
}

function eventLabel(event: string): string {
  return event.split("_").map((part) => part[0].toUpperCase() + part.slice(1)).join(" ");
}

function DevicePage({ id, onBack }: { id: number; onBack: () => void }) {
  const [device, setDevice] = useState<Device | null>(null);
  const [history, setHistory] = useState<DeviceEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);

  const load = useCallback(async () => {
    try {
      const [nextDevice, nextHistory] = await Promise.all([api.device(id), api.history(id)]);
      setDevice(nextDevice);
      setHistory(nextHistory);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load device");
    }
  }, [id]);

  useEffect(() => { void load(); }, [load]);

  const rescanPorts = async () => {
    setScanning(true);
    setError(null);
    try { await api.scanPorts(id); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Port scan failed"); }
    finally { setScanning(false); }
  };

  if (error && !device) return <div className="notice error-notice">{error} <button className="link-button" onClick={onBack}>Return to devices</button></div>;
  if (!device) return <div className="empty-state"><span className="loader" /> Loading device…</div>;

  return (
    <>
      <button className="back-button" onClick={onBack}><ArrowLeft size={16} /> All devices</button>
      <section className="device-hero">
        <div className="device-avatar"><Cpu size={27} /></div>
        <div>
          <div className="title-line"><h1>{device.hostname || "Unknown device"}</h1>{device.is_new && <span className="new-badge">New</span>}</div>
          <span className={`status ${device.status}`}><i />{device.status}</span>
        </div>
      </section>
      {error && <div className="notice error-notice">{error}</div>}

      <section className="detail-grid">
        <Info icon={<Globe2 />} label="IP address" value={device.ip} mono />
        <Info icon={<Network />} label="MAC address" value={device.mac} mono />
        <Info icon={<Cpu />} label="Vendor" value={device.vendor} />
        <Info icon={<Clock3 />} label="First seen" value={exactTime(device.first_seen)} />
        <Info icon={<Clock3 />} label="Last seen" value={exactTime(device.last_seen)} />
      </section>

      <div className="two-column">
        <section className="panel section-panel">
          <div className="section-header"><div><h2>Open ports</h2><p>TCP services accepting connections.</p></div><button className="secondary-button" disabled={scanning} onClick={rescanPorts}><Radar size={15} className={scanning ? "spin" : ""} />{scanning ? "Scanning…" : "Rescan ports"}</button></div>
          {device.open_ports?.length ? (
            <table className="ports-table"><thead><tr><th>Port</th><th>Service</th><th>State</th></tr></thead><tbody>{device.open_ports.map((port) => <tr key={port.port}><td className="mono">{port.port}</td><td>{port.service}</td><td><span className="open-state"><i />Open</span></td></tr>)}</tbody></table>
          ) : <div className="small-empty">No open ports found.</div>}
        </section>

        <section className="panel section-panel">
          <div className="section-header"><div><h2>History</h2><p>Changes observed across network scans.</p></div></div>
          {history.length ? <ol className="timeline">{history.map((event) => <li key={event.id}><i /><div><strong>{eventLabel(event.event)}</strong><p>{event.detail}</p><time>{exactTime(event.occurred_at)}</time></div></li>)}</ol> : <div className="small-empty">No history recorded.</div>}
        </section>
      </div>
    </>
  );
}

function Info({ icon, label, value, mono = false }: { icon: React.ReactNode; label: string; value: string; mono?: boolean }) {
  return <div className="info-item"><span>{icon}</span><div><small>{label}</small><strong className={mono ? "mono" : ""}>{value}</strong></div></div>;
}

export default DevicePage;

