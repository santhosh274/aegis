import { Sparkline, type SparklinePoint } from "./Sparkline";
import { cn } from "../lib/utils";

/**
 * Top-stats card: large number + label with a small sparkline showing the last
 * 7 runs' trend. A pulsing dot indicates an active scan when `pulsing` is set.
 */
export function MetricCard({
  label,
  value,
  trend,
  pulsing = false,
  accent = "cyan",
  hint,
}: {
  label: string;
  value: string | number;
  trend?: number[] | SparklinePoint[];
  pulsing?: boolean;
  accent?: "cyan" | "green" | "regression";
  hint?: string;
}) {
  const color =
    accent === "green"
      ? "text-success"
      : accent === "regression"
        ? "text-regression"
        : "text-cyan";

  return (
    <div className="flex flex-col justify-between gap-3 rounded-xl border border-border bg-card p-4">
      <div className="flex items-center gap-2">
        {pulsing && <span className="blink-dot cyan" />}
        <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          {label}
        </span>
      </div>
      <div className={cn("text-3xl font-semibold tabular-nums", color)}>{value}</div>
      <div className="flex items-center justify-between gap-2">
        {trend && trend.length > 0 ? (
          <Sparkline data={trend} />
        ) : (
          <span className="text-[11px] text-muted-foreground/60">no trend data</span>
        )}
        {hint && <span className="text-[11px] text-muted-foreground">{hint}</span>}
      </div>
    </div>
  );
}