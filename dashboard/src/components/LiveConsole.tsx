import { useState, useRef, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Terminal, Trash2, Lock, Unlock } from "lucide-react";
import type { LogEntry, LogLevel } from "../data/mockData";
import { logEntries as initialLogs } from "../data/mockData";

const levelStyles: Record<LogLevel, { text: string; tag: string }> = {
  INFO: { text: "text-text-secondary", tag: "text-text-muted" },
  WARN: { text: "text-[#a1a1aa]", tag: "text-text-secondary" },
  ERROR: { text: "text-white", tag: "text-white" },
  SUCCESS: { text: "text-text-secondary", tag: "text-white" },
};

const filters: (LogLevel | "ALL")[] = ["ALL", "INFO", "WARN", "ERROR", "SUCCESS"];

export default function LiveConsole() {
  const [levelFilter, setLevelFilter] = useState<LogLevel | "ALL">("ALL");
  const [autoScroll, setAutoScroll] = useState(true);
  const [logs, setLogs] = useState<LogEntry[]>(initialLogs);
  const consoleRef = useRef<HTMLDivElement>(null);

  const filteredLogs = useMemo(
    () =>
      levelFilter === "ALL" ? logs : logs.filter((l) => l.level === levelFilter),
    [logs, levelFilter]
  );

  useEffect(() => {
    if (autoScroll && consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [filteredLogs, autoScroll]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLogs((prev) => [
        ...prev,
        {
          timestamp: new Date().toISOString().slice(11, 23),
          level: "INFO" as LogLevel,
          source: "core.planner",
          message: "Re-evaluating utility rankings after exploitation results...",
        },
      ]);
      setTimeout(() => {
        setLogs((prev) => [
          ...prev,
          {
            timestamp: new Date(Date.now() + 2000).toISOString().slice(11, 23),
            level: "INFO" as LogLevel,
            source: "utility_ranker",
            message: "Action candidates refreshed. Next: rce_validation (U=0.88)",
          },
        ]);
      }, 3000);
    }, 6000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="panel flex flex-col h-full">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-white" strokeWidth={1.5} />
          <span className="label">Live Console</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className="p-1.5 hover:bg-[#0f0f0f] transition-colors cursor-pointer"
            title={autoScroll ? "Unlock scroll" : "Lock scroll"}
          >
            {autoScroll ? (
              <Lock className="w-3 h-3 text-white" strokeWidth={1.5} />
            ) : (
              <Unlock className="w-3 h-3 text-text-muted" strokeWidth={1.5} />
            )}
          </button>
          <button
            onClick={() => setLogs([])}
            className="p-1.5 hover:bg-[#0f0f0f] transition-colors cursor-pointer"
            title="Clear logs"
          >
            <Trash2 className="w-3 h-3 text-text-muted hover:text-white" strokeWidth={1.5} />
          </button>
        </div>
      </div>

      <div className="px-4 py-2 border-b border-border flex items-center gap-1">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setLevelFilter(f)}
            className={`px-2 py-0.5 text-[10px] font-mono font-semibold tracking-wider transition-colors cursor-pointer ${
              levelFilter === f
                ? f === "ALL"
                  ? "bg-white text-black"
                  : "bg-white text-black"
                : "text-text-muted hover:text-white"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div
        ref={consoleRef}
        className="flex-1 min-h-[320px] max-h-[520px] overflow-y-auto p-4 font-mono text-[11px] leading-[1.8]"
        style={{ background: "#000000" }}
      >
        {filteredLogs.length === 0 && (
          <div className="text-text-muted text-center py-12">
            No log entries.
          </div>
        )}
        {filteredLogs.map((log, i) => (
          <motion.div
            key={`${log.timestamp}-${i}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-3 py-px hover:bg-[#0a0a0a]"
          >
            <span className="text-text-muted flex-shrink-0 select-none">
              {log.timestamp}
            </span>
            <span
              className={`flex-shrink-0 font-semibold w-16 ${levelStyles[log.level].tag}`}
            >
              [{log.level}]
            </span>
            <span className="text-text-muted flex-shrink-0">{log.source}</span>
            <span className={levelStyles[log.level].text}>{log.message}</span>
          </motion.div>
        ))}
        <div className="flex items-center gap-1.5 mt-2">
          <span className="text-text-muted">$</span>
          <span className="w-2 h-3.5 bg-white blink" />
        </div>
      </div>
    </div>
  );
}
