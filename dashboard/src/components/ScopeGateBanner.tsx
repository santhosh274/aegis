import { ShieldCheck, ShieldOff } from "lucide-react";
import type { ScopeSettings } from "../api/client";

/**
 * Persistent scope-policy gate banner shown at the top of the app. It is always
 * visible (incl. exploit/verify screens) and reads from live scope settings.
 */
export function ScopeGateBanner({ scope }: { scope: ScopeSettings | null }) {
  const labOn = scope?.lab_mode ?? false;
  const hosts = scope?.allowed_hosts ?? [];
  const plugins = scope?.allowed_plugins ?? [];
  const exploitAllowed = plugins.includes("vsftpd_backdoor");

  return (
    <div
      className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-border bg-surface px-4 py-1.5"
      data-testid="scope-gate"
    >
      <span
        className={`inline-flex items-center gap-1.5 font-mono text-[11px] font-bold uppercase tracking-wider ${
          labOn ? "text-success" : "text-destructive"
        }`}
      >
        {labOn ? <ShieldCheck className="size-3.5" /> : <ShieldOff className="size-3.5" />}
        Lab Mode: {labOn ? "ON" : "OFF"}
      </span>
      <span className="font-mono text-[11px] text-muted-foreground">
        Allowed:{" "}
        <span className="text-foreground">
          {hosts.length ? hosts.join(", ") : "none"}
        </span>
      </span>
      <span className="font-mono text-[11px] text-muted-foreground">
        Plugin:{" "}
        <span className={exploitAllowed ? "text-danger" : "text-muted-foreground"}>
          {plugins.includes("vsftpd_backdoor") ? "vsftpd_backdoor" : "—"}
        </span>
      </span>
      {!labOn && (
        <span className="ml-auto text-[11px] font-medium text-warning">
          Exploit and verify phases are disabled until Lab Mode is toggled on in
          Settings.
        </span>
      )}
    </div>
  );
}