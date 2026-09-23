import { useState } from "react";
import { Link } from "react-router-dom";
import { Activity, ArrowRight, Plus } from "lucide-react";
import { useAegisStore } from "../store/useAegisStore";
import { selectVerificationQueue } from "../store/useAegisStore";
import { MetricCard } from "../components/MetricCard";
import { PipelineVisualizer } from "../components/PipelineVisualizer";
import { VerificationQueue } from "../components/VerificationQueue";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { LifecycleChip } from "../components/LifecycleChip";
import { FindingDrawer } from "../components/FindingDrawer";
import { severityChip } from "../lib/severity";
import { trendFor, distinctTargets } from "../lib/trends";
import { formatTime } from "../lib/utils";
import type { Finding } from "../api/client";

function FeedRow({ finding, onOpen }: { finding: Finding; onOpen: () => void }) {
  const sev = severityChip(finding);
  return (
    <button
      onClick={onOpen}
      className="finding-new flex w-full items-center gap-3 rounded-md border border-border bg-surface px-3 py-2.5 text-left transition-colors hover:border-muted-foreground/50"
    >
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium">{finding.title}</div>
        <div className="mt-0.5 flex flex-wrap items-center gap-2">
          <span className="font-mono text-[11px] text-cyan">{finding.target}</span>
          <span className="font-mono text-[10px] text-muted-foreground">
            {formatTime(finding.created_at)}
          </span>
        </div>
      </div>
      <span
        className={`shrink-0 rounded border px-1.5 py-0.5 font-mono text-[10px] font-bold ${sev.className}`}
      >
        {sev.label}
      </span>
      <LifecycleChip status={finding.status} className="shrink-0" />
      <ConfidenceBadge grade={finding.confidence} className="shrink-0" />
    </button>
  );
}

export default function Dashboard() {
  const findings = useAegisStore((s) => s.findings);
  const status = useAegisStore((s) => s.status);
  const phases = useAegisStore((s) => s.phases);
  const pipelineEvents = useAegisStore((s) => s.pipelineEvents);
  const [selected, setSelected] = useState<Finding | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const openFinding = (f: Finding) => {
    setSelected(f);
    setDrawerOpen(true);
  };

  const queue = selectVerificationQueue(findings);
  const closed = findings.filter((f) => f.status === "verified_closed");
  const openCount = findings.filter((f) => f.status !== "verified_closed").length;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Live MAPE-K-V pipeline, finding feed and verification queue.
          </p>
        </div>
        <Link
          to="/run"
          className="inline-flex h-9 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus /> New scan
        </Link>
      </div>

      {/* Top stats row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Active Targets"
          value={distinctTargets(findings)}
          pulsing={status.active_scan}
          trend={trendFor(findings, () => true)}
        />
        <MetricCard
          label="Open Findings"
          value={openCount}
          trend={trendFor(findings, (f) => f.status !== "verified_closed")}
        />
        <MetricCard
          label="Awaiting Verification"
          value={queue.length}
          accent="regression"
          trend={trendFor(
            findings,
            (f) => f.status === "confirmed" || f.status === "reopened"
          )}
        />
        <MetricCard
          label="Confirmed Closed"
          value={closed.length}
          accent="green"
          trend={trendFor(findings, (f) => f.status === "verified_closed")}
          hint="vs ADAPT baseline"
        />
      </div>

      {/* Live pipeline */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="mb-2 flex items-center gap-2">
          <Activity className="size-4 text-cyan" />
          <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Live MAPE-K-V Pipeline
          </h2>
          {status.active_scan || status.active_exploit || status.active_verify ? (
            <span className="ml-1 rounded border border-cyan/40 bg-cyan/10 px-1.5 py-0.5 font-mono text-[10px] text-cyan">
              ACTIVE
            </span>
          ) : (
            <span className="ml-1 rounded border border-border bg-elevated px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              IDLE
            </span>
          )}
        </div>
        <PipelineVisualizer phases={phases} events={pipelineEvents} />
      </div>

      {/* Finding feed + verification queue */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="rounded-xl border border-border bg-card">
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Finding Feed
              </h2>
              <span className="font-mono text-[10px] text-muted-foreground">
                {findings.length} total
              </span>
            </div>
            <div className="flex max-h-[520px] flex-col gap-2 overflow-y-auto p-3">
              {findings.length === 0 && (
                <p className="py-10 text-center text-sm text-muted-foreground">
                  No findings yet — run a discovery scan or exploit chain to get started.
                </p>
              )}
              {findings.map((f) => (
                <FeedRow key={f.id} finding={f} onOpen={() => openFinding(f)} />
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card">
          <div className="flex items-center justify-between border-b border-border px-5 py-3">
            <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Verification Queue
            </h2>
            <Link
              to="/verification"
              className="inline-flex items-center gap-1 font-mono text-[10px] text-cyan hover:underline"
            >
              open <ArrowRight className="size-3" />
            </Link>
          </div>
          <div className="max-h-[520px] overflow-y-auto p-3">
            <VerificationQueue findings={queue} onOpen={openFinding} />
          </div>
        </div>
      </div>

      <FindingDrawer
        finding={selected}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
      />
    </div>
  );
}