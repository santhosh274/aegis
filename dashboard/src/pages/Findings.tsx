import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ListFilter, Search } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card } from "../components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "../components/ui/table";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { LifecycleChip } from "../components/LifecycleChip";
import { FindingDrawer } from "../components/FindingDrawer";
import { api, type ConfidenceGrade, type Finding, type FindingStatus } from "../api/client";
import { formatDate } from "../lib/utils";
import { cn } from "../lib/utils";

const CONFIDENCE_OPTIONS: Array<{ value: ConfidenceGrade; label: string }> = [
  { value: "confirmed", label: "Confirmed" },
  { value: "suspected", label: "Suspected" },
  { value: "needs_human_review", label: "Needs Review" },
];

const STATUS_OPTIONS: Array<{ value: FindingStatus; label: string }> = [
  { value: "open", label: "Opened" },
  { value: "confirmed", label: "Confirmed" },
  { value: "remediated", label: "Remediated" },
  { value: "verified_closed", label: "Verified Closed" },
  { value: "reopened", label: "Reopened" },
  { value: "needs_human_review", label: "Needs Review" },
];

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-full border px-2.5 py-1 font-mono text-[11px] font-medium transition-colors",
        active
          ? "border-primary bg-primary/15 text-primary"
          : "border-border bg-surface text-muted-foreground hover:border-muted-foreground/50"
      )}
    >
      {children}
    </button>
  );
}

export default function Findings() {
  const { data: findings = [] } = useQuery({
    queryKey: ["findings"],
    queryFn: api.getFindings,
  });
  const { data: history = [] } = useQuery({
    queryKey: ["verify-history"],
    queryFn: api.getVerificationHistory,
  });

  const [confFilters, setConfFilters] = useState<ConfidenceGrade[]>([]);
  const [statusFilter, setStatusFilter] = useState<FindingStatus | "all">("all");
  const [ipFilter, setIpFilter] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const [selected, setSelected] = useState<Finding | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const lastVerifiedAt = useMemo(() => {
    const map = new Map<string, string>();
    for (const row of history) {
      if (!map.has(row.finding_id)) map.set(row.finding_id, row.timestamp);
    }
    return map;
  }, [history]);

  const filtered = useMemo(() => {
    return findings.filter((f) => {
      if (confFilters.length > 0 && !confFilters.includes(f.confidence)) return false;
      if (statusFilter !== "all" && f.status !== statusFilter) return false;
      if (ipFilter && !f.target.includes(ipFilter.trim())) return false;
      if (fromDate && new Date(f.created_at) < new Date(`${fromDate}T00:00:00`)) return false;
      if (toDate && new Date(f.created_at) > new Date(`${toDate}T23:59:59`)) return false;
      return true;
    });
  }, [findings, confFilters, statusFilter, ipFilter, fromDate, toDate]);

  const toggleConf = (c: ConfidenceGrade) =>
    setConfFilters((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    );

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Findings</h1>
        <p className="text-sm text-muted-foreground">
          {filtered.length} of {findings.length} findings shown.
        </p>
      </div>

      <Card className="gap-3 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
            <ListFilter className="size-3.5" /> Filter
          </span>
          <div className="flex flex-wrap gap-2">
            {CONFIDENCE_OPTIONS.map((c) => (
              <Chip
                key={c.value}
                active={confFilters.includes(c.value)}
                onClick={() => toggleConf(c.value)}
              >
                {c.label}
              </Chip>
            ))}
            {STATUS_OPTIONS.map((s) => (
              <Chip
                key={s.value}
                active={statusFilter === s.value}
                onClick={() =>
                  setStatusFilter(statusFilter === s.value ? "all" : s.value)
                }
              >
                {s.label}
              </Chip>
            ))}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Target IP"
              value={ipFilter}
              onChange={(e) => setIpFilter(e.target.value)}
              className="w-44 pl-8 font-mono text-xs"
            />
          </div>
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            From
            <Input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="h-8 w-40"
            />
          </label>
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            To
            <Input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="h-8 w-40"
            />
          </label>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setConfFilters([]);
              setStatusFilter("all");
              setIpFilter("");
              setFromDate("");
              setToDate("");
            }}
          >
            Reset
          </Button>
        </div>
      </Card>

      <Card className="gap-0 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-surface">
              <TableHead>Target</TableHead>
              <TableHead>Vulnerability</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Lifecycle</TableHead>
              <TableHead>Discovered</TableHead>
              <TableHead>Last Verified</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="py-10 text-center text-sm text-muted-foreground">
                  No findings match the current filters.
                </TableCell>
              </TableRow>
            )}
            {filtered.map((f) => (
              <TableRow key={f.id} className="cursor-pointer">
                <TableCell className="font-mono text-xs text-cyan">{f.target}</TableCell>
                <TableCell className="max-w-[280px]">
                  <span className="block truncate text-sm">{f.title}</span>
                </TableCell>
                <TableCell>
                  <ConfidenceBadge grade={f.confidence} />
                </TableCell>
                <TableCell>
                  <LifecycleChip status={f.status} />
                </TableCell>
                <TableCell className="font-mono text-[11px] text-muted-foreground">
                  {formatDate(f.created_at)}
                </TableCell>
                <TableCell className="font-mono text-[11px] text-muted-foreground">
                  {f.verification_verdict
                    ? formatDate(lastVerifiedAt.get(f.id))
                    : "—"}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelected(f);
                      setDrawerOpen(true);
                    }}
                  >
                    Open
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      <FindingDrawer
        finding={selected}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
      />
    </div>
  );
}