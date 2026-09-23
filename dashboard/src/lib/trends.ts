import type { Finding } from "../api/client";

/**
 * Computes per-run sparkline trends from the findings archive: the last `n`
 * runs (buckets) and, for each bucket, the number of findings matching the
 * given predicate. Mirrors "last 7 runs' trend" on the dashboard stats row.
 */
function runBuckets(findings: Finding[], n: number): Finding[][] {
  const sorted = [...findings].sort((a, b) =>
    a.created_at.localeCompare(b.created_at)
  );
  if (sorted.length === 0) return [];
  const buckets: Finding[][] = Array.from({ length: n }, () => []);
  const per = Math.max(1, Math.ceil(sorted.length / n));
  sorted.forEach((f, i) => {
    const b = Math.min(n - 1, Math.floor(i / per));
    buckets[b].push(f);
  });
  return buckets;
}

export function trendFor(
  findings: Finding[],
  predicate: (f: Finding) => boolean,
  n = 7
): number[] {
  return runBuckets(findings, n).map((b) => b.filter(predicate).length);
}

export function distinctTargets(findings: Finding[]): number {
  return new Set(findings.map((f) => f.target)).size;
}