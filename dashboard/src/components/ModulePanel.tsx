import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { modules as allModules } from "../data/mockData";

interface ModulePanelProps {
  moduleStates: Record<string, boolean>;
  onToggle: (id: string) => void;
}

const stageGroups = [
  "Service Scanning",
  "Initial Exploitation",
  "Corroboration",
  "Post-Exploitation",
  "Report Generation",
];

export default function ModulePanel({ moduleStates, onToggle }: ModulePanelProps) {
  const [expandedStage, setExpandedStage] = useState<string | null>(
    "Initial Exploitation"
  );

  return (
    <div className="panel">
      <div className="px-4 py-3 border-b border-border">
        <span className="label">Module Control</span>
      </div>

      <div>
        {stageGroups.map((stage) => {
          const stageModules = allModules.filter((m) => m.stage === stage);
          const isExpanded = expandedStage === stage;

          return (
            <div key={stage} className="border-b border-border last:border-b-0">
              <button
                onClick={() =>
                  setExpandedStage(isExpanded ? null : stage)
                }
                className="w-full flex items-center justify-between px-4 py-3 text-[11px] font-semibold text-text-secondary hover:bg-[#0f0f0f] transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <ChevronRight
                    className={`w-3 h-3 text-text-muted transition-transform duration-200 ${
                      isExpanded ? "rotate-90" : ""
                    }`}
                    strokeWidth={2}
                  />
                  <span className="tracking-widest">{stage.toUpperCase()}</span>
                  <span className="text-text-muted font-normal">
                    ({stageModules.length})
                  </span>
                </div>
              </button>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="overflow-hidden"
                  >
                    <div className="border-t border-border">
                      {stageModules.map((mod) => {
                        const enabled = moduleStates[mod.id] ?? mod.enabled;
                        return (
                          <div
                            key={mod.id}
                            className="flex items-center justify-between px-4 py-2.5 hover:bg-[#0f0f0f] transition-colors border-b border-border last:border-b-0"
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`text-[11px] font-mono ${
                                    enabled ? "text-white" : "text-text-muted"
                                  }`}
                                >
                                  {mod.name}
                                </span>
                                <span className="text-[9px] font-mono text-text-muted px-1.5 py-0.5 bg-badge-bg border border-border">
                                  {mod.file}
                                </span>
                              </div>
                            </div>
                            <button
                              onClick={() => onToggle(mod.id)}
                              className="ml-3 flex-shrink-0 cursor-pointer group"
                            >
                              <div
                                className={`w-7 h-4 rounded-sm flex items-center transition-colors ${
                                  enabled
                                    ? "bg-white justify-end"
                                    : "bg-border justify-start"
                                }`}
                              >
                                <motion.div
                                  layout
                                  className={`w-3 h-3 rounded-[1px] mx-0.5 ${
                                    enabled ? "bg-black" : "bg-text-muted"
                                  }`}
                                />
                              </div>
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </div>
  );
}
