import { useState } from "react";
import { Plus, Save, X } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Checkbox } from "../components/ui/checkbox";
import { Switch } from "../components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useAegisStore } from "../store/useAegisStore";
import { useLiveData } from "../hooks/useLiveData";
import { isValidIpv4 } from "../lib/utils";

const PLUGIN_ROSTER = [
  { id: "nmap_scanner", label: "nmap_scanner", hint: "service discovery", enabled: true },
  { id: "vsftpd_backdoor", label: "vsftpd_backdoor", hint: "exploit adapter", enabled: true },
  { id: "rce_validation", label: "rce_validation", hint: "devil's-advocate corroboration", enabled: true },
];

// Known adapters that are explicitly out of scope — always greyed out.
const DISABLED_PLUGINS = [
  { id: "hydra", label: "hydra", hint: "credential brute-force" },
  { id: "sqlmap", label: "sqlmap", hint: "SQL injection" },
  { id: "metasploit", label: "metasploit", hint: "framework" },
  { id: "service_discovery", label: "service_discovery", hint: "scanner" },
  { id: "data_exposure", label: "data_exposure", hint: "corroboration" },
  { id: "privilege_escalation", label: "privilege_escalation", hint: "corroboration" },
  { id: "weak_credentials", label: "weak_credentials", hint: "corroboration" },
  { id: "lateral_movement", label: "lateral_movement", hint: "post-exploitation" },
  { id: "persistence", label: "persistence", hint: "post-exploitation" },
];

export default function Settings() {
  const scope = useAegisStore((s) => s.scope);
  const { saveSettingsAndRefresh } = useLiveData();
  const [ok, setOk] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [hostInput, setHostInput] = useState("");

  if (!scope) {
    return (
      <Card>
        <CardContent className="pt-6 text-sm text-muted-foreground">
          Loading scope settings…
        </CardContent>
      </Card>
    );
  }

  const [hosts, setHosts] = useState<string[]>(scope.allowed_hosts);
  const [plugins, setPlugins] = useState<string[]>(scope.allowed_plugins);
  const [labMode, setLabMode] = useState(scope.lab_mode);
  const [ports, setPorts] = useState(scope.ports);
  const [listenerPort, setListenerPort] = useState(String(scope.listener_port));
  const [connectT, setConnectT] = useState(String(scope.timeouts.connect));
  const [listenT, setListenT] = useState(String(scope.timeouts.listen));
  const [replayT, setReplayT] = useState(String(scope.timeouts.replay_wait));

  const addHost = () => {
    const ip = hostInput.trim();
    if (!isValidIpv4(ip)) {
      setErr("Host must be a valid IPv4 address.");
      return;
    }
    if (hosts.includes(ip)) {
      setHostInput("");
      return;
    }
    setHosts([...hosts, ip]);
    setHostInput("");
    setErr(null);
  };

  const togglePlugin = (id: string, checked: boolean) => {
    setPlugins((prev) =>
      checked ? [...prev, id] : prev.filter((p) => p !== id)
    );
  };

  const save = async () => {
    setErr(null);
    setOk(null);
    try {
      await saveSettingsAndRefresh({
        allowed_hosts: hosts,
        allowed_plugins: plugins,
        lab_mode: labMode,
        ports: ports.trim() || "21-23,80",
        listener_port: Number(listenerPort) || 6200,
        timeouts: {
          connect: Number(connectT) || 5,
          listen: Number(listenT) || 8,
          replay_wait: Number(replayT) || 5,
        },
      });
      setOk("Scope policy saved to config/scope.json.");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Save failed.");
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Scope policy and port configuration written to config/scope.json.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Scope policy */}
        <Card className="gap-5">
          <CardHeader className="pb-0">
            <CardTitle className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              Scope Policy
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            <div className="flex flex-col gap-2">
              <Label>Allowed hosts</Label>
              <div className="flex flex-wrap items-center gap-2 rounded-md border border-border bg-surface p-2">
                {hosts.map((h) => (
                  <span
                    key={h}
                    className="inline-flex items-center gap-1 rounded border border-border bg-elevated px-2 py-0.5 font-mono text-[11px]"
                  >
                    {h}
                    <button
                      onClick={() => setHosts(hosts.filter((x) => x !== h))}
                      className="text-muted-foreground hover:text-destructive"
                      aria-label={`remove ${h}`}
                    >
                      <X className="size-3" />
                    </button>
                  </span>
                ))}
                <input
                  value={hostInput}
                  onChange={(e) => setHostInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addHost();
                    }
                  }}
                  placeholder="192.168.52.139"
                  className="flex-1 bg-transparent px-1 font-mono text-xs outline-none placeholder:text-muted-foreground"
                />
              </div>
              <Button size="sm" variant="outline" onClick={addHost} className="w-fit">
                <Plus /> Add host
              </Button>
            </div>

            <div className="flex flex-col gap-2">
              <Label>Allowed plugins</Label>
              <div className="flex flex-col gap-2">
                {PLUGIN_ROSTER.map((p) => (
                  <label
                    key={p.id}
                    className="flex items-center gap-3 rounded-md border border-border bg-surface px-3 py-2"
                  >
                    <Checkbox
                      checked={plugins.includes(p.id)}
                      onCheckedChange={(c) => togglePlugin(p.id, c === true)}
                    />
                    <div className="text-sm">
                      <div className="font-mono font-semibold">{p.label}</div>
                      <div className="text-xs text-muted-foreground">{p.hint}</div>
                    </div>
                  </label>
                ))}
                {DISABLED_PLUGINS.map((p) => (
                  <label
                    key={p.id}
                    className="flex items-center gap-3 rounded-md border border-border bg-surface px-3 py-2 opacity-45"
                    aria-disabled
                  >
                    <Checkbox checked={false} disabled />
                    <div className="text-sm">
                      <div className="font-mono font-semibold">{p.label}</div>
                      <div className="text-xs text-muted-foreground">{p.hint}</div>
                    </div>
                  </label>
                ))}
              </div>
              <p className="text-[11px] text-muted-foreground">
                Out-of-scope plugins are greyed out and cannot be enabled.
              </p>
            </div>

            <div className="flex items-center justify-between rounded-md border border-border bg-surface px-3 py-2.5">
              <div>
                <Label>Lab mode</Label>
                <p className="text-xs text-muted-foreground">
                  Must be ON for exploit and verify phases to run.
                </p>
              </div>
              <Switch
                checked={labMode}
                onCheckedChange={(c) => {
                  setLabMode(c);
                  if (!c) {
                    setPlugins((prev) =>
                      prev.filter((p) => p !== "vsftpd_backdoor")
                    );
                  }
                }}
              />
            </div>

            <Button onClick={save} className="w-fit">
              <Save /> Save policy
            </Button>
          </CardContent>
        </Card>

        {/* Port configuration */}
        <Card className="gap-5">
          <CardHeader className="pb-0">
            <CardTitle className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              Port Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            <div className="flex flex-col gap-2">
              <Label htmlFor="ports">Target port list (discovery)</Label>
              <Input
                id="ports"
                value={ports}
                onChange={(e) => setPorts(e.target.value)}
                className="font-mono text-xs"
              />
              <p className="text-[11px] text-muted-foreground">
                Nmap scan range for the discover phase. Defaults to DEFAULT_PORTS.
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="listener">Listener port (corroboration)</Label>
              <Input
                id="listener"
                type="number"
                value={listenerPort}
                onChange={(e) => setListenerPort(e.target.value)}
                className="h-9 w-32 font-mono text-xs"
              />
              <p className="text-[11px] text-muted-foreground">
                Port the corroboration listener expects (vsftpd backdoor: 6200).
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {[
                { key: "connect", label: "Connect (s)", value: connectT, set: setConnectT },
                { key: "listen", label: "Listen (s)", value: listenT, set: setListenT },
                { key: "replay_wait", label: "Replay wait (s)", value: replayT, set: setReplayT },
              ].map((t) => (
                <div key={t.key} className="flex flex-col gap-2">
                  <Label htmlFor={`timeout-${t.key}`}>{t.label}</Label>
                  <Input
                    id={`timeout-${t.key}`}
                    type="number"
                    value={t.value}
                    onChange={(e) => t.set(e.target.value)}
                    className="font-mono text-xs"
                  />
                </div>
              ))}
            </div>

            {err && (
              <p className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                {err}
              </p>
            )}
            {ok && (
              <p className="rounded-md border border-success/50 bg-success/10 p-3 text-sm text-success">
                {ok}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}