import { useState } from "react";
import { Download, Play, Wrench } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "./ui/sheet";
import { Button } from "./ui/button";
import { Separator } from "./ui/separator";
import { ScrollArea } from "./ui/scroll-area";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { LifecycleChip } from "./LifecycleChip";
import { LifecycleTimeline } from "./LifecycleTimeline";
import { formatTime } from "../lib/utils";
import { useNavigate } from "react-router-dom";
import { api, type Finding } from "../api/client";
import { useQueryClient } from "@tanstack/react-query";
import type { Corroboration } from "../api/client";

const OUTCOME_STYLE: Record<Corroboration["outcome"], string> = {
  supports: "text-success border-success/50 bg-success/10",
  contradicts: "text-destructive border-destructive/50 bg-destructive/10",
  ambiguous: "text-warning border-warning/50 bg-warning/10",
};

function cveFrom(title: string): string | null {
  const m = title.match(/CVE-\d{4}-\d{4,}/i);
  return m ? m[0] : null;
}

function toPath(finding: Finding): string | null {
  const p = finding._path;
  if (p) return p;
  const key = finding.scenario ?? finding.id;
  return `evaluation/results/${key}.json`;
}

export function FindingDrawer({
  finding,
  open,
  onOpenChange,
}: {
  finding: Finding | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  if (!finding) return null;
  const cve = cveFrom(finding.title);

  const markRemediated = async () => {
    setBusy("remediate");
    try {
      await api.remediate(finding.id);
      await queryClient.invalidateQueries({ queryKey: ["findings"] });
    } catch (err) {
      console.error(err);
    } finally {
      setBusy(null);
    }
  };

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(finding, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${finding.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl lg:max-w-2xl">
        <SheetHeader className="pr-8">
          <SheetTitle className="text-base leading-snug">{finding.title}</SheetTitle>
          <SheetDescription className="flex flex-wrap items-center gap-2">
            {cve && <span className="cve-text">{cve}</span>}
            <span className="font-mono text-xs text-muted-foreground">{finding.target}</span>
            <span className="font-mono text-xs text-muted-foreground">
              discovered {formatTime(finding.created_at)}
            </span>
          </SheetDescription>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <ConfidenceBadge grade={finding.confidence} size="lg" />
            <LifecycleChip status={finding.status} />
          </div>
        </SheetHeader>

        <ScrollArea className="flex-1 px-6 min-h-0">
          <div className="flex flex-col gap-6 pb-6">
            <section>
              <h3 className="mb-2 font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Claim
              </h3>
              <p className="text-sm text-foreground/85">{finding.claim}</p>
            </section>

            <Separator />

            <section>
              <h3 className="mb-2 font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Primary Evidence
              </h3>
              <div className="terminal-log p-3 text-xs">
                <div className="text-muted-foreground">
                  <span className="text-border">//</span> source:{" "}
                  <span className="text-cyan">{finding.primary_evidence.source}</span>
                </div>
                <div>{finding.primary_evidence.summary}</div>
                <div className="text-muted-foreground">
                  kind: {finding.primary_evidence.kind}
                </div>
              </div>
            </section>

            <Separator />

            <section>
              <h3 className="mb-2 font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Corroboration
              </h3>
              {finding.corroborations.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No independent corroboration recorded for this finding.
                </p>
              ) : (
                <div className="flex flex-col gap-2">
                  {finding.corroborations.map((c, i) => (
                    <div
                      key={i}
                      className="flex items-start justify-between gap-3 rounded-md border border-border bg-surface p-3"
                    >
                      <div className="min-w-0">
                        <div className="font-mono text-xs font-semibold">{c.probe}</div>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {c.evidence.summary}
                        </p>
                        {c.rationale && (
                          <p className="mt-1 text-xs text-muted-foreground/70">
                            rationale: {c.rationale}
                          </p>
                        )}
                      </div>
                      <span
                        className={`shrink-0 rounded border px-2 py-0.5 font-mono text-[10px] font-bold uppercase ${OUTCOME_STYLE[c.outcome]}`}
                      >
                        {c.outcome}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <Separator />

            <section>
              <h3 className="mb-2 font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Attack Chain
              </h3>
              <div className="flex flex-col">
                {finding.attack_chain.map((step, i) => (
                  <div key={step.id} className="relative flex gap-3 pb-4 last:pb-0">
                    {i < finding.attack_chain.length - 1 && (
                      <div className="absolute left-[11px] top-6 bottom-0 w-px bg-border" />
                    )}
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-border bg-elevated font-mono text-[10px] text-muted-foreground">
                      {i + 1}
                    </div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-semibold">{step.plugin}</span>
                        <span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                          {step.action}
                        </span>
                      </div>
                      <p className="mt-1 font-mono text-xs text-muted-foreground">
                        target: {step.target} · predicate: {step.expected_predicate}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <Separator />

            <section>
              <h3 className="mb-3 font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Lifecycle Timeline
              </h3>
              <LifecycleTimeline finding={finding} />
            </section>
          </div>
        </ScrollArea>

        <div className="flex flex-wrap gap-2 border-t border-border p-4">
          <Button
            size="sm"
            variant="outline"
            disabled={finding.status === "remediated" || busy === "remediate"}
            onClick={markRemediated}
          >
            <Wrench /> Mark Remediated
          </Button>
          <Button
            size="sm"
            disabled={
              finding.status !== "confirmed" && finding.status !== "reopened"
            }
            onClick={() => {
              onOpenChange(false);
              navigate(`/verification?finding=${finding.id}`);
            }}
          >
            <Play /> Run Verification
          </Button>
          <Button size="sm" variant="ghost" onClick={exportJson}>
            <Download /> Export Finding JSON
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}

export { toPath };