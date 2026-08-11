import { motion } from "framer-motion";
import {
  Search,
  Crosshair,
  Bug,
  Rocket,
  FileBarChart,
} from "lucide-react";
import type { PipelineStage, NodeStatus } from "../data/mockData";

interface PipelineVisualizerProps {
  stages: PipelineStage[];
}

const stageIcons: Record<string, React.ReactNode> = {
  "stage-1": <Search className="w-4 h-4" strokeWidth={1.5} />,
  "stage-2": <Crosshair className="w-4 h-4" strokeWidth={1.5} />,
  "stage-3": <Bug className="w-4 h-4" strokeWidth={1.5} />,
  "stage-4": <Rocket className="w-4 h-4" strokeWidth={1.5} />,
  "stage-5": <FileBarChart className="w-4 h-4" strokeWidth={1.5} />,
};

const statusStyles: Record<
  NodeStatus,
  { border: string; text: string; dot: string; bg: string }
> = {
  idle: {
    border: "border-border border-dashed",
    text: "text-text-muted",
    dot: "bg-text-muted",
    bg: "bg-surface",
  },
  running: {
    border: "border-white",
    text: "text-white",
    dot: "bg-white pulse-dot",
    bg: "bg-surface",
  },
  success: {
    border: "border-white",
    text: "text-white",
    dot: "bg-white",
    bg: "bg-white",
  },
  failed: {
    border: "border-text-muted",
    text: "text-text-secondary",
    dot: "bg-text-muted",
    bg: "bg-surface",
  },
};

function formatDuration(ms: number | null): string {
  if (ms === null) return "--";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export default function PipelineVisualizer({ stages }: PipelineVisualizerProps) {
  return (
    <div className="panel p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="label">Execution Pipeline</span>
      </div>

      <div className="flex items-stretch gap-0 overflow-x-auto">
        {stages.map((stage, i) => {
          const cfg = statusStyles[stage.status];
          const isRunning = stage.status === "running";
          const isSuccess = stage.status === "success";

          return (
            <div key={stage.id} className="flex items-center">
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                className={`relative border ${cfg.border} bg-surface p-3 min-w-[140px] transition-all duration-300`}
              >
                {isRunning && (
                  <motion.div
                    className="absolute top-0 left-0 h-[2px] bg-white"
                    animate={{ width: ["0%", "100%", "0%"] }}
                    transition={{
                      repeat: Infinity,
                      duration: 2.5,
                      ease: "easeInOut",
                    }}
                  />
                )}

                <div className="flex items-center gap-2 mb-2">
                  <div className={cfg.text}>{stageIcons[stage.id]}</div>
                  <span className="text-[11px] font-bold text-white tracking-wide">
                    {stage.name}
                  </span>
                </div>

                <div className="flex flex-wrap gap-1 mb-2">
                  {stage.modules.map((mod) => (
                    <span
                      key={mod}
                      className="text-[9px] font-mono px-1.5 py-0.5 bg-badge-bg text-text-muted border border-border"
                    >
                      {mod}
                    </span>
                  ))}
                </div>

                <div className="flex items-center justify-between text-[10px] font-mono">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                    <span className={cfg.text}>
                      {stage.status.toUpperCase()}
                    </span>
                  </div>
                  <span className="text-text-muted">
                    {isRunning
                      ? `${stage.latency}ms`
                      : formatDuration(stage.duration)}
                  </span>
                </div>

                {isSuccess && (
                  <div className="absolute top-0 left-0 w-full h-[2px] bg-white" />
                )}
              </motion.div>

              {i < stages.length - 1 && (
                <div className="flex items-center px-1">
                  <div
                    className={`w-4 h-[1px] ${
                      isSuccess ? "bg-white" : "bg-border border-dashed"
                    }`}
                  />
                  <div
                    className={`w-0 h-0 border-t-[3px] border-t-transparent border-b-[3px] border-b-transparent border-l-[5px] ${
                      isSuccess ? "border-l-white" : "border-l-border"
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
