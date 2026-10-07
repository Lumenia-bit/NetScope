import { useEffect, useState } from "react";
import { Check, RotateCcw } from "lucide-react";
import { api } from "./api";
import type { Settings } from "./types";

function SettingsPage({ onSaved }: { onSaved: () => void }) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [ports, setPorts] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.settings().then((value) => { setSettings(value); setPorts(value.ports.join(", ")); }).catch((err: Error) => setError(err.message));
  }, []);

  if (!settings) return <div className="empty-state"><span className="loader" /> Loading settings…</div>;

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    const parsedPorts = ports.split(/[\s,]+/).filter(Boolean).map(Number);
    if (parsedPorts.some((port) => !Number.isInteger(port))) { setError("Ports must be whole numbers separated by commas."); return; }
    setSaving(true); setError(null);
    try { await api.updateSettings({ ...settings, subnet: settings.subnet?.trim() || null, ports: parsedPorts }); onSaved(); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not save settings"); }
    finally { setSaving(false); }
  };

  return (
    <>
      <section className="page-heading"><div><p className="eyebrow">Configuration</p><h1>Settings</h1><p>Control how NetScope discovers and inspects local devices.</p></div></section>
      <form className="panel settings-form" onSubmit={save}>
        {error && <div className="notice error-notice">{error}</div>}
        <div className="form-section"><h2>Network</h2><p>Leave the subnet empty to use the automatically detected local network.</p><label><span>Subnet override</span><input value={settings.subnet ?? ""} onChange={(event) => setSettings({ ...settings, subnet: event.target.value })} placeholder="192.168.1.0/24" /><small>IPv4 private networks up to /16 are supported.</small></label></div>
        <div className="form-section"><h2>Port scanning</h2><label><span>Default TCP ports</span><textarea rows={3} value={ports} onChange={(event) => setPorts(event.target.value)} /><small>Comma- or space-separated ports. Up to 128 ports.</small></label><label className="compact-field"><span>Connection timeout</span><div className="input-suffix"><input type="number" min="0.05" max="10" step="0.05" value={settings.scan_timeout} onChange={(event) => setSettings({ ...settings, scan_timeout: Number(event.target.value) })} /><b>seconds</b></div></label></div>
        <div className="form-section"><h2>Device details</h2><Toggle label="Resolve hostnames" description="Use local reverse DNS to find device names." checked={settings.resolve_hostnames} onChange={(checked) => setSettings({ ...settings, resolve_hostnames: checked })} /><Toggle label="Look up vendors" description="Match MAC prefixes against the bundled local OUI database." checked={settings.vendor_lookup} onChange={(checked) => setSettings({ ...settings, vendor_lookup: checked })} /></div>
        <div className="form-actions"><button type="button" className="secondary-button" onClick={() => { setSettings({ ...settings, subnet: null }); setError(null); }}><RotateCcw size={15} />Use detected network</button><button className="primary-button" disabled={saving}><Check size={16} />{saving ? "Saving…" : "Save settings"}</button></div>
      </form>
    </>
  );
}

function Toggle({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return <label className="toggle-row"><span><strong>{label}</strong><small>{description}</small></span><input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} /><i /></label>;
}

export default SettingsPage;

