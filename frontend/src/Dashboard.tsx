import { useMemo, useState } from "react";
import { ArrowUpDown, CircleDot, Network, Search, ShieldCheck, Unplug } from "lucide-react";
import type { Device } from "./types";

interface Props {
  devices: Device[];
  loading: boolean;
  onNavigate: (path: string) => void;
}

type SortKey = "status" | "hostname" | "ip" | "vendor" | "last_seen";

function relativeTime(value: string): string {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 10) return "now";
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function ipNumber(ip: string): number {
  return ip.split(".").reduce((total, octet) => total * 256 + Number(octet), 0);
}

function Dashboard({ devices, loading, onNavigate }: Props) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [vendor, setVendor] = useState("all");
  const [sort, setSort] = useState<SortKey>("status");
  const [ascending, setAscending] = useState(true);

  const vendors = useMemo(
    () => [...new Set(devices.map((device) => device.vendor))].sort(),
    [devices],
  );

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return devices
      .filter((device) => status === "all" || device.status === status)
      .filter((device) => vendor === "all" || device.vendor === vendor)
      .filter((device) =>
        !needle || [device.hostname, device.ip, device.mac, device.vendor]
          .some((value) => value?.toLowerCase().includes(needle)),
      )
      .sort((a, b) => {
        let comparison: number;
        if (sort === "ip") comparison = ipNumber(a.ip) - ipNumber(b.ip);
        else if (sort === "status") comparison = a.status === b.status ? 0 : a.status === "online" ? -1 : 1;
        else comparison = String(a[sort] ?? "").localeCompare(String(b[sort] ?? ""));
        return ascending ? comparison : -comparison;
      });
  }, [devices, query, status, vendor, sort, ascending]);

  const changeSort = (key: SortKey) => {
    if (key === sort) setAscending((value) => !value);
    else { setSort(key); setAscending(true); }
  };

  const online = devices.filter((device) => device.status === "online").length;
  const newDevices = devices.filter((device) => device.is_new).length;
  const openPorts = devices.reduce((total, device) => total + device.ports.length, 0);

  return (
    <>
      <section className="page-heading">
        <div>
          <p className="eyebrow">Local network</p>
          <h1>Devices</h1>
          <p>Hosts discovered on your network and their current reachability.</p>
        </div>
      </section>

      <section className="stats-grid" aria-label="Network summary">
        <Stat icon={<CircleDot />} label="Devices online" value={online} tone="green" />
        <Stat icon={<Network />} label="Total devices" value={devices.length} />
        <Stat icon={<ShieldCheck />} label="New devices" value={newDevices} tone="blue" />
        <Stat icon={<Unplug />} label="Open ports" value={openPorts} tone="amber" />
      </section>

      <section className="panel device-panel">
        <div className="toolbar">
          <label className="search-field">
            <Search size={16} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search devices" aria-label="Search devices" />
          </label>
          <div className="filter-group">
            <select value={status} onChange={(event) => setStatus(event.target.value)} aria-label="Filter by status">
              <option value="all">All statuses</option>
              <option value="online">Online</option>
              <option value="offline">Offline</option>
            </select>
            {vendors.length > 1 && (
              <select value={vendor} onChange={(event) => setVendor(event.target.value)} aria-label="Filter by vendor">
                <option value="all">All vendors</option>
                {vendors.map((name) => <option key={name}>{name}</option>)}
              </select>
            )}
          </div>
        </div>

        {loading ? (
          <div className="empty-state"><span className="loader" /> Loading devices…</div>
        ) : devices.length === 0 ? (
          <div className="empty-state">
            <RadarEmpty />
            <h2>No devices discovered yet</h2>
            <p>Run your first network scan to find devices on this subnet.</p>
          </div>
        ) : visible.length === 0 ? (
          <div className="empty-state"><h2>No matching devices</h2><p>Try changing your search or filters.</p></div>
        ) : (
          <div className="table-scroll">
            <table className="device-table">
              <thead><tr>
                <Sortable label="Status" column="status" current={sort} onClick={changeSort} />
                <Sortable label="Device" column="hostname" current={sort} onClick={changeSort} />
                <Sortable label="IP" column="ip" current={sort} onClick={changeSort} />
                <th>MAC</th>
                <Sortable label="Vendor" column="vendor" current={sort} onClick={changeSort} />
                <th>Open ports</th>
                <Sortable label="Last seen" column="last_seen" current={sort} onClick={changeSort} />
              </tr></thead>
              <tbody>
                {visible.map((device) => (
                  <tr key={device.id} tabIndex={0} onClick={() => onNavigate(`/devices/${device.id}`)} onKeyDown={(event) => event.key === "Enter" && onNavigate(`/devices/${device.id}`)}>
                    <td data-label="Status"><span className={`status ${device.status}`}><i />{device.status}</span></td>
                    <td data-label="Device"><span className="device-name">{device.hostname || "Unknown device"}</span>{device.is_new && <span className="new-badge">New</span>}</td>
                    <td data-label="IP" className="mono">{device.ip}</td>
                    <td data-label="MAC" className="mono muted">{device.mac}</td>
                    <td data-label="Vendor">{device.vendor}</td>
                    <td data-label="Open ports">{device.ports.length ? <span className="ports">{device.ports.join(", ")}</span> : <span className="muted">—</span>}</td>
                    <td data-label="Last seen" title={new Date(device.last_seen).toLocaleString()}>{relativeTime(device.last_seen)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

function Stat({ icon, label, value, tone = "default" }: { icon: React.ReactNode; label: string; value: number; tone?: string }) {
  return <div className="stat"><span className={`stat-icon ${tone}`}>{icon}</span><div><strong>{value}</strong><span>{label}</span></div></div>;
}

function Sortable({ label, column, current, onClick }: { label: string; column: SortKey; current: SortKey; onClick: (key: SortKey) => void }) {
  return <th><button className={current === column ? "sort active" : "sort"} onClick={() => onClick(column)}>{label}<ArrowUpDown size={12} /></button></th>;
}

function RadarEmpty() {
  return <div className="empty-radar"><span /><span /><i /></div>;
}

export default Dashboard;
