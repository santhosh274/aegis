import { motion } from "framer-motion";
import {
  Activity,
  Play,
  FileText,
  Shield,
} from "lucide-react";

interface HeaderProps {
  isRunning: boolean;
  onRunPipeline: () => void;
  onExport: () => void;
}

export default function Header({ isRunning, onRunPipeline, onExport }: HeaderProps) {
  return (
    <header className="panel px-5 py-3 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
      <div className="flex items-center gap-5">
        <div className="flex items-center gap-2.5">
          <Shield className="w-5 h-5 text-white" strokeWidth={1.5} />
          <h1 className="text-sm font-bold tracking-tight whitespace-nowrap">
            CYBERPIPE
            <span className="text-text-muted font-normal ml-2">
              // PIPELINE ENGINE
            </span>
          </h1>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-1 border border-border">
            {isRunning && (
              <span className="w-1.5 h-1.5 rounded-full bg-white pulse-dot" />
            )}
            <span className="tracking-widest text-xs">
              {isRunning ? "RUNNING" : "IDLE"}
            </span>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-3 text-[11px] font-mono text-text-secondary">
          <span>
            TARGET <span className="text-white">10.0.0.0/24</span>
          </span>
          <span className="text-border">|</span>
          <span>
            CRIT <span className="text-white">2</span>
          </span>
          <span className="text-border">|</span>
          <span>
            HIGH <span className="text-white">2</span>
          </span>
          <span className="text-border">|</span>
          <span>
            MED <span className="text-white">2</span>
          </span>
          <span className="text-border">|</span>
          <span>
            LOW <span className="text-white">1</span>
          </span>
        </div>

        <div className="flex items-center gap-2">
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={onRunPipeline}
            disabled={isRunning}
            className="ghost-btn-primary flex items-center gap-2"
          >
            <Play className="w-3 h-3" strokeWidth={2.5} />
            Run Pipeline
          </motion.button>
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={onExport}
            className="ghost-btn flex items-center gap-2"
          >
            <FileText className="w-3 h-3" strokeWidth={1.5} />
            Export Report
          </motion.button>
        </div>
      </div>
    </header>
  );
}
