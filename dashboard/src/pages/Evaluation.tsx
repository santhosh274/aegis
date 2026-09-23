import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Download, Play, RefreshCw } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "../components/ui/table";
import { usePipelineRun, extractEventData } from "../hooks/usePipelineRun";
import {
  api,
  type EvaluationReport,
  type Verdict,
} from "../api/client";
import { cn } from "../lib/utils";

type ScenarioRow = {
  scenario: string;
  expected_verdict?: Verdict;
  verification_verdict?: Verdict;
  status?: string;
  confidence?: string;
  ground_truth_exploitable?: boolean;
  ground_truth_fixed?: boolean;
  description?: string;
};

const METRIC_KEYS = [
  "total_findings",
  "false_positive_rate_adapt_baseline",
  "false_positive_rate_aegis",
  "fp_reduction_percent",
  "confidence_accuracy",
  "confidence_confusion",
  "verification_accuracy",
  "false_all_clear_rate",
  "verification_confusion",
] as const;

const VERDICT_COLORS: Record<Verdict, string> = {
  verified_closed: "#3DDC84",
  reopened: "#FF5A36",
  regression_detected: "#FF8C42",
  inconclusive: "#8B909A",
};

const VERDICT_ORDER: Verdict[] = [
  "verified_closed",
  "reopened",
  "regression_detected",
  "inconclusive",
];

function pct(x: number | undefined): string {
  if (x === undefined) return "—";
  return `${(x * 100).toFixed(1)}%`;
}

export default function Evaluation() {
  const { run, running, events } = usePipelineRun();
  const [ran, setRan] = useState(false);

  // Derive the report incrementally as each metric event arrives (live updates).
  const report = useMemo(() => {
    if (!ran) return null as Partial<EvaluationReport> | null;
    let acc: Partial<EvaluationReport> = {};
    for (const ev of events) {
      const d = ev.data;
      if (!d) continue;
      for (const k of METRIC_KEYS) {
        if (k in d) (acc as Record<string, unknown>)[k] = d[k];
      }
    }
    return acc;
  }, [events, ran]);

  const scenarios = useMemo<ScenarioRow[]>(() => {
    const rows = extractEventData<ScenarioRow[]>(events, "scenarios") ?? [];
    return rows.map((r) => ({ ...r }));
  }, [events]);

  const runEvaluation = async () => {
    setRan(true);
    await run("/evaluation/metrics", {});
  };

  const exportReport = async () => {
    const res = await fetch("/api/evaluation/report");
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      alert(body.detail ?? "Report not available — run evaluation first.");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "metrics.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  // Stacked verification data per scenario.
  const verificationStack = useMemo(() => {
    return scenarios.map((s) => {
      const row: Record<string, string | number> = { scenario: s.scenario };
      for (const v of VERDICT_ORDER) {
        row[v] = s.verification_verdict === v ? 1 : 0;
      }
      return row;
    });
  }, [scenarios]);

  const adaptFp = report?.false_positive_rate_adapt_baseline;
  const aegisFp = report?.false_positive_rate_aegis;
  const fpData = [
    { name: "False-Positive Rate", ADAPT: adaptFp, AEGIS: aegisFp },
  ];
  const confAcc = report?.confidence_accuracy;
  const confData = [
    { name: "Correct", value: confAcc ?? 0 },
    { name: "Incorrect", value: confAcc === undefined ? 1 : 1 - confAcc },
  ];
  const verAcc = report?.verification_accuracy;
  const facr = report?.false_all_clear_rate;
  const hasData = adaptFp !== undefined || confAcc !== undefined || scenarios.length > 0;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Evaluation</h1>
          <p className="text-sm text-muted-foreground">
            AEGIS vs ADAPT baseline metrics from the evaluation harness.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={exportReport}>
            <Download /> Export Report
          </Button>
          <Button onClick={runEvaluation} disabled={running}>
            {running ? (
              <>
                <RefreshCw className="animate-spin" /> Running…
              </>
            ) : (
              <>
                <Play /> Run Evaluation
              </>
            )}
          </Button>
        </div>
      </div>

      {!hasData && !running && (
        <Card>
          <CardContent className="pt-6 text-sm text-muted-foreground">
            No evaluation data yet — press "Run Evaluation" to stream the metrics
            from evaluation/results/.
          </CardContent>
        </Card>
      )}

      {(hasData || running) && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {/* 1 — False-positive rate reduction */}
          <Card className="gap-3">
            <CardHeader className="pb-0">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                False-Positive Rate Reduction
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <div className="h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={fpData} layout="vertical">
                    <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} hide />
                    <YAxis type="category" dataKey="name" width={10} tickLine={false} axisLine={false} tick={false} />
                    <Tooltip
                      formatter={(value: unknown, name: unknown) => [
                        `${(Number(value) * 100).toFixed(1)}%`,
                        String(name),
                      ]}
                      contentStyle={{ background: "#1c2028", border: "1px solid #2A2E38", borderRadius: 6, fontSize: 12 }}
                      labelStyle={{ color: "#8B909A" }}
                    />
                    <Bar dataKey="ADAPT" fill="#2A2E38" barSize={14} radius={[4, 4, 4, 4]} />
                    <Bar dataKey="AEGIS" fill="#3DD6F5" barSize={14} radius={[4, 4, 4, 4]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono text-muted-foreground">
                  ADAPT {pct(adaptFp)} vs AEGIS {pct(aegisFp)}
                </span>
                <span className="font-mono text-success">
                  −{report?.fp_reduction_percent ?? "—"}%
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground">vs ADAPT baseline.</p>
            </CardContent>
          </Card>

          {/* 2 — Confidence grading accuracy */}
          <Card className="gap-3">
            <CardHeader className="pb-0">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Confidence Grading Accuracy
              </CardTitle>
            </CardHeader>
            <CardContent className="relative flex flex-col items-center gap-2">
              <div className="relative h-44 w-44">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={confData}
                      dataKey="value"
                      innerRadius={58}
                      outerRadius={80}
                      paddingAngle={2}
                      stroke="none"
                      isAnimationActive={false}
                    >
                      <Cell fill="#3DDC84" />
                      <Cell fill="#2A2E38" />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-semibold tabular-nums">
                    {pct(confAcc).replace("%", "")}%
                  </span>
                  <span className="text-[10px] text-muted-foreground">correct</span>
                </div>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Correct vs incorrect grades across all scenarios.
              </p>
            </CardContent>
          </Card>

          {/* 3 — Remediation verification accuracy */}
          <Card className="gap-3">
            <CardHeader className="pb-0">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Remediation Verification Accuracy
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <div className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={verificationStack} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                    <XAxis dataKey="scenario" tick={{ fontSize: 9, fill: "#8B909A" }} axisLine={false} tickLine={false} />
                    <YAxis hide domain={[0, 1]} />
                    <Tooltip
                      contentStyle={{ background: "#1c2028", border: "1px solid #2A2E38", borderRadius: 6, fontSize: 12 }}
                      labelStyle={{ color: "#8B909A" }}
                    />
                    {VERDICT_ORDER.map((v) => (
                      <Bar key={v} dataKey={v} stackId="a" fill={VERDICT_COLORS[v]} isAnimationActive={false} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono text-muted-foreground">
                  Accuracy {pct(verAcc)}
                </span>
                <span className="font-mono text-destructive">
                  False all-clear {pct(facr)}
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground">
                verified_closed / reopened / regression / inconclusive per scenario.
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {(hasData || scenarios.length > 0) && (
        <Card className="gap-0 overflow-hidden">
          <CardHeader className="border-b border-border">
            <CardTitle className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              Scenario Results
            </CardTitle>
          </CardHeader>
          <Table>
            <TableHeader>
              <TableRow className="bg-surface">
                <TableHead>Scenario</TableHead>
                <TableHead>Expected Verdict</TableHead>
                <TableHead>AEGIS Verdict</TableHead>
                <TableHead>Match</TableHead>
                <TableHead>Ground Truth</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {scenarios.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="py-8 text-center text-sm text-muted-foreground">
                    No scenario results yet.
                  </TableCell>
                </TableRow>
              )}
              {scenarios.map((s, i) => {
                const match =
                  s.expected_verdict && s.verification_verdict === s.expected_verdict;
                return (
                  <TableRow key={i}>
                    <TableCell className="font-mono text-xs">{s.scenario}</TableCell>
                    <TableCell className="font-mono text-xs">{s.expected_verdict ?? "—"}</TableCell>
                    <TableCell className="font-mono text-xs">
                      <span
                        className={cn(
                          "rounded border px-1.5 py-0.5 text-[10px] font-bold",
                          s.verification_verdict === "verified_closed" &&
                            "border-success/50 bg-success/10 text-success",
                          s.verification_verdict === "reopened" &&
                            "border-destructive/50 bg-destructive/10 text-destructive",
                          s.verification_verdict === "regression_detected" &&
                            "border-regression/50 bg-regression/10 text-regression",
                          s.verification_verdict === "inconclusive" &&
                            "border-border bg-elevated text-muted-foreground"
                        )}
                      >
                        {s.verification_verdict ?? "—"}
                      </span>
                    </TableCell>
                    <TableCell>
                      {match === undefined ? (
                        <span className="text-muted-foreground">—</span>
                      ) : match ? (
                        <span className="text-success">✅</span>
                      ) : (
                        <span className="text-destructive">❌</span>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {s.ground_truth_fixed === undefined
                        ? "—"
                        : s.ground_truth_fixed
                          ? "fixed"
                          : "not fixed"}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}