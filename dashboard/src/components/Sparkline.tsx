import { Line, LineChart, ResponsiveContainer, YAxis } from "recharts";

export interface SparklinePoint {
  x: string | number;
  y: number;
}

/** Minimal Recharts sparkline for top-stats trend cards (last 7 runs). */
export function Sparkline({
  data,
  color = "#3DD6F5",
  height = 28,
}: {
  data: number[] | SparklinePoint[];
  color?: string;
  height?: number;
}) {
  const points: SparklinePoint[] = data.map((d, i) =>
    typeof d === "number" ? { x: i, y: d } : d
  );
  return (
    <div style={{ width: "100%", height, minWidth: 72 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
          <YAxis hide domain={["dataMin", "dataMax"]} />
          <Line
            type="monotone"
            dataKey="y"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}