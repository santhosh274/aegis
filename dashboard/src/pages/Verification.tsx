import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  HelpCircle,
  Play,
  RotateCcw,
  TerminalSquare,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "../components/ui/table";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { TerminalLog } from "../components/TerminalLog";
import { usePipelineRun, extractEventData } from "../hooks/usePipelineRun";
import { useAegisStore } from "../store/useAegisStore";
import {
  api,
  type Finding,
  type VerificationResult,
  type Verdict,
  type VerificationHistoryRow,
} from "../api/client";
import { cn, formatTime } from "../lib/utils";

const VERDICT_META: Record<
  Verdict,
  { label: string; icon: React.ReactNode; tone: string }
> = {
  verified_closed: {
    label: "Verified Closed",
    icon: <CheckCircle2 className="size-5" />,
    tone: "verified_closed",
  },
  reopened: {
    label: "Reopened",
    icon: <RotateCcw className="size-5" />,
    tone: "reopened",
  },
  regression_detected: {
    label: "Regression Detected",
    icon: <AlertTriangle className="size-5" />,
    tone: "regression_detected",
  },
  inconclusive: {
    label: "Inconclusive",
    icon: <HelpCircle className="size-5" />,
    tone: "inconclusive",
  },
};

const VERDICT_WHY: Record<Verdict, string> = {
  verified_closed:
    "The controls check passed, the exposure snapshot shows the service no longer present, and the replay of the original exploit chain failed to regain access — the finding is verified closed.",
  reopened:
    "Replay of the original exploit chain succeeded after remediation — the vulnerability is still present and the finding is reopened.",
  regression_detected:
    "The exposure snapshot still shows an at-risk service after remediation — regression detected.",
  inconclusive:
    "The controls check or replay could not be completed with sufficient certainty — more investigation is required.",
};

export default function Verification() {
  const [params, setParams] = useSearchParams();
  const findings = useAegisStore((s) => s.findings);
  const { run, running, events, error } = usePipelineRun();

  const pending = useMemo(
    () =>
      findings.filter(
        (f) => f.status === "confirmed" || f.status === "reopened"
      ),
    [findings]
  );

  const [selected, setSelected] = useState<Finding | null>(null);
  const [beforePath, setBeforePath] = useState("");
  const [beforeWarning, setBeforeWarning] = useState<string | null>(null);
  const [verification, setVerification] = useState<VerificationResult | null>(null);

  const { data: history = [] } = useQuery({
    queryKey: ["verify-history"],
    queryFn: api.getVerificationHistory,
  });

  // Open the finding referenced by ?finding=<id>
  useEffect(() => {
    const id = params.get("finding");
    if (!id) return;
    const f = findings.find((x) => x.id === id);
    if (f) {
      selectFinding(f);
      setParams({}, { replace: true });
    }
  }, [params, findings]);

  const selectFinding = async (f: Finding) => {
    setSelected(f);
    setVerification(null);
    setBeforeWarning(null);
    try {
      const res = await api.snapshotBeforeExists(f.target);
      if (res.exists) {
        setBeforePath(res.saved_to ?? "before.json");
      } else {
        setBeforePath("");
        setBeforeWarning("Capture snapshot first — no before.json exists for this target.");
      }
    } catch {
      setBeforeWarning("Could not check for an existing before snapshot.");
    }
  };

  const runVerification = async () => {
    setVerification(null);
    const findingPath = selected?._path ?? `evaluation/results/${selected?.id}.json`;
    const collected = await run("/verify/run", {
      target: selected?.target,
      finding_path: findingPath,
      before_path: beforePath,
    });
    const v = extractEventData<VerificationResult>(collected, "verification");
    if (v) setVerification(v);
  };

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Verification</h1>
        <p className="text-sm text-muted-foreground">
          Corroborate remediation closure by replaying the exploit chain the way
          the CLI verification script does.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Left — pending verification */}
        <div className="flex flex-col gap-3">
          <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Pending Verification
          </h2>
          {pending.length === 0 && (
            <Card>
              <CardContent className="pt-6 text-sm text-muted-foreground">
                No findings currently await verification.
              </CardContent>
            </Card>
          )}
          {pending.map((f) => (
            <button
              key={f.id}
              onClick={() => selectFinding(f)}
              className={cn(
                "flex items-center justify-between gap-3 rounded-md border border-border bg-card p-4 text-left transition-colors hover:border-muted-foreground/50",
                selected?.id === f.id && "border-primary/60"
              )}
            >
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">{f.title}</div>
                <div className="mt-1 font-mono text-[11px] text-muted-foreground">
                  {f.target}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <ConfidenceBadge grade={f.confidence} />
                <Button size="sm" onClick={() => selectFinding(f)}>
                  <Play /> Start Verification
                </Button>
              </div>
            </button>
          ))}
        </div>

        {/* Right — run verification */}
        <div className="flex flex-col gap-4">
          {!selected ? (
            <Card>
              <CardContent className="pt-6 text-sm text-muted-foreground">
                Select a finding from the pending list to run verification, or press
                "Start Verification" on a finding.
              </CardContent>
            </Card>
          ) : (
            <>
              <Card className="gap-4">
                <CardHeader className="pb-0">
                  <CardTitle className="text-sm">{selected.title}</CardTitle>
                  <p className="font-mono text-xs text-muted-foreground">
                    {selected.target} · {selected.id.slice(0, 8)}
                  </p>
                </CardHeader>
                <CardContent className="flex flex-col gap-4">
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="before">Before snapshot path</Label>
                    <Input
                      id="before"
                      value={beforePath}
                      onChange={(e) => {
                        setBeforePath(e.target.value);
                        setBeforeWarning(null);
                      }}
                      placeholder="before.json"
                      className="font-mono text-xs"
                    />
                    {beforeWarning && (
                      <p className="text-xs text-warning">{beforeWarning}</p>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={async () => {
                        try {
                          const res = await api.captureSnapshot(selected.target, "before");
                          setBeforePath(res.saved_to);
                          setBeforeWarning(null);
                        } catch (err) {
                          setBeforeWarning(
                            err instanceof Error ? err.message : "Snapshot failed."
                          );
                        }
                      }}
                    >
                      <Camera /> Capture Before Snapshot
                    </Button>
                    <Button size="sm" onClick={runVerification} disabled={running || !beforePath}>
                      <Play /> Run Verification
                    </Button>
                  </div>

                  <div className="rounded-md border border-border bg-surface p-3">
                    <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                      <TerminalSquare className="size-3.5" /> Apply Remediation on VM
                    </div>
                    <p className="mt-2 text-sm text-foreground/85">
                      Stop the backdoored service on the target before verifying (lab VM
                      only):
                    </p>
                    <pre className="terminal-log mt-2 p-2.5 text-xs">
                      sudo service vsftpd stop
                    </pre>
                  </div>
                </CardContent>
              </Card>

              {events.length > 0 && (
                <TerminalLog events={events} maxHeight={240} />
              )}
              {error && (
                <p className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
                </p>
              )}

              {verification && (
                <Card className="gap-3">
                  <CardHeader className="pb-0">
                    <CardTitle className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                      Verdict
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-3">
                    <div
                      className={cn(
                        "verdict-badge self-start",
                        VERDICT_META[verification.verdict].tone
                      )}
                    >
                      {VERDICT_META[verification.verdict].icon}
                      {VERDICT_META[verification.verdict].label}
                    </div>
                    <p className="text-sm text-foreground/85">
                      {VERDICT_WHY[verification.verdict]}
                    </p>
                    <div className="terminal-log p-3 text-xs">
                      <div className="text-muted-foreground">
                        <span className="text-border">//</span> evidence
                      </div>
                      <div>{verification.evidence.summary}</div>
                      {verification.failed_step_id && (
                        <div className="text-muted-foreground">
                          failed step: {verification.failed_step_id}
                        </div>
                      )}
                    </div>
                    {verification.regression_summary && (
                      <div className="rounded-md border border-regression/50 bg-regression/10 p-3 text-sm font-medium text-regression">
                        Regression detail: {verification.regression_summary}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>

      {/* Bottom — verification history */}
      <Card className="gap-0 overflow-hidden">
        <CardHeader className="border-b border-border">
          <CardTitle className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Verification History
          </CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow className="bg-surface">
              <TableHead>Finding</TableHead>
              <TableHead>Verdict</TableHead>
              <TableHead>Target State</TableHead>
              <TableHead>Timestamp</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {history.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="py-8 text-center text-sm text-muted-foreground">
                  No verification runs recorded yet.
                </TableCell>
              </TableRow>
            )}
            {history.map((row: VerificationHistoryRow, i) => (
              <TableRow key={i}>
                <TableCell className="max-w-[280px]">
                  <span className="block truncate text-sm">{row.finding_title}</span>
                </TableCell>
                <TableCell>
                  <span
                    className={cn(
                      "inline-flex items-center gap-1 rounded border px-2 py-0.5 font-mono text-[10px] font-bold",
                      row.verdict === "verified_closed" &&
                        "border-success/50 bg-success/10 text-success",
                      row.verdict === "reopened" &&
                        "border-destructive/50 bg-destructive/10 text-destructive",
                      row.verdict === "regression_detected" &&
                        "border-regression/50 bg-regression/10 text-regression",
                      row.verdict === "inconclusive" &&
                        "border-border bg-elevated text-muted-foreground"
                    )}
                  >
                    {VERDICT_META[row.verdict].label}
                  </span>
                </TableCell>
                <TableCell className="font-mono text-[11px] text-muted-foreground">
                  {row.target_state}
                </TableCell>
                <TableCell className="font-mono text-[11px] text-muted-foreground">
                  {formatTime(row.timestamp)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}