import { motion } from "framer-motion";
import { Cpu, Globe, BarChart3 } from "lucide-react";

interface GaugeProps {
  label: string;
  value: number;
  max: number;
  icon: React.ReactNode;
}

function RadialGauge({ label, value, max, icon }: GaugeProps) {
  const pct = Math.min((value / max) * 100, 100);
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-[80px] h-[80px]">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
          <circle
            cx="40"
            cy="40"
            r={radius}
            fill="none"
            stroke="#262626"
            strokeWidth="4"
          />
          <motion.circle
            cx="40"
            cy="40"
            r={radius}
            fill="none"
            stroke="#ffffff"
            strokeWidth="4"
            strokeLinecap="square"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.2, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-base font-bold font-mono text-white">
            {Math.round(pct)}%
          </span>
        </div>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-text-muted">{icon}</span>
        <span className="label">{label}</span>
      </div>
    </div>
  );
}

export default function ResourceGauges() {
  return (
    <div className="panel p-4">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-3.5 h-3.5 text-text-muted" strokeWidth={1.5} />
        <span className="label">Telemetry</span>
      </div>

      <div className="flex items-center justify-around">
        <RadialGauge
          label="Threads"
          value={14}
          max={16}
          icon={<Cpu className="w-3 h-3" strokeWidth={1.5} />}
        />
        <RadialGauge
          label="Response"
          value={92}
          max={100}
          icon={<Globe className="w-3 h-3" strokeWidth={1.5} />}
        />
        <RadialGauge
          label="Progress"
          value={38}
          max={100}
          icon={<BarChart3 className="w-3 h-3" strokeWidth={1.5} />}
        />
      </div>
    </div>
  );
}
