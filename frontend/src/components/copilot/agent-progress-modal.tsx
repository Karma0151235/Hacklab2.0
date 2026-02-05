import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  FileText,
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  steps: AgentStep[];
}

export interface AgentStep {
  id: string;
  name: string;
  description: string;
  status: "waiting" | "running" | "completed" | "skipped" | "error";
  logs: string[];
  icon: any;
}

export function AgentProgressModal({
  isOpen,
  onClose,
  steps,
}: AgentProgressModalProps) {
  const [selectedAgent, setSelectedAgent] = useState<string>("supervisor");

  // Auto-select running agent
  useEffect(() => {
    const runningStep = steps.find((s) => s.status === "running");
    if (runningStep) {
      setSelectedAgent(runningStep.id);
    }
  }, [steps]);

  const currentStep = steps.find((s) => s.id === selectedAgent) || steps[0];
  const activeAgent = steps.find((s) => s.status === "running")?.id;
  const progressPercent = getProgressPercent(currentStep.status);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-bg-primary/80 backdrop-blur-sm"
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="relative h-[640px] w-full max-w-5xl overflow-hidden rounded-2xl border border-border-secondary bg-bg-secondary shadow-2xl"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border-secondary px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-primary/10">
                <Loader2 className="h-5 w-5 animate-spin text-accent-primary" />
              </div>
              <div>
                <h2 className="font-sans text-lg font-bold text-text-primary">
                  Agent Orchestration
                </h2>
                <p className="font-sans text-xs text-text-tertiary">
                  Live backend progress and logs
                </p>
              </div>
            </div>
            {/* 
               We usually disable closing while loading, but for UX freedom let's allow minimizing 
               or just show it's working. For now, strict modal.
            */}
          </div>

          <div className="flex h-[calc(100%-80px)] flex-col">
            {/* Workflow canvas */}
            <div className="relative flex flex-1 flex-col gap-6 p-6">
              <div className="rounded-2xl border border-border-secondary bg-bg-tertiary/30 p-6">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-text-secondary">
                      Multi-Agent Workflow
                    </h3>
                    <p className="text-xs text-text-tertiary">
                      Real-time orchestration with active flow
                    </p>
                  </div>
                  <StatusBadge status={currentStep.status} />
                </div>

                <div className="relative flex flex-col items-center gap-8 py-6">
                  {/* Flow lines */}
                  <svg className="absolute inset-0 h-full w-full overflow-visible">
                    {activeAgent === "rag" ? (
                      <motion.path
                        d="M50% 32% L50% 58%"
                        stroke="currentColor"
                        className="stroke-blue-400 drop-shadow-[0_0_10px_rgba(59,130,246,0.95)]"
                        strokeWidth="2.5"
                        strokeDasharray="6 6"
                        animate={{ strokeDashoffset: [12, 0] }}
                        transition={{
                          repeat: Infinity,
                          duration: 1.1,
                          ease: "linear",
                        }}
                      />
                    ) : (
                      <path
                        d="M50% 32% L50% 58%"
                        stroke="currentColor"
                        className="stroke-border-secondary"
                        strokeWidth="2"
                        strokeDasharray="4 4"
                      />
                    )}
                    {activeAgent === "financial" ? (
                      <motion.path
                        d="M25% 58% L25% 78%"
                        stroke="currentColor"
                        className="stroke-emerald-400 drop-shadow-[0_0_10px_rgba(52,211,153,0.95)]"
                        strokeWidth="2.5"
                        strokeDasharray="6 6"
                        animate={{ strokeDashoffset: [12, 0] }}
                        transition={{
                          repeat: Infinity,
                          duration: 1.1,
                          ease: "linear",
                        }}
                      />
                    ) : (
                      <path
                        d="M25% 58% L25% 78%"
                        stroke="currentColor"
                        className="stroke-border-secondary"
                        strokeWidth="2"
                        strokeDasharray="4 4"
                      />
                    )}
                    {activeAgent === "alert" ? (
                      <motion.path
                        d="M75% 58% L75% 78%"
                        stroke="currentColor"
                        className="stroke-amber-400 drop-shadow-[0_0_10px_rgba(251,191,36,0.95)]"
                        strokeWidth="2.5"
                        strokeDasharray="6 6"
                        animate={{ strokeDashoffset: [12, 0] }}
                        transition={{
                          repeat: Infinity,
                          duration: 1.1,
                          ease: "linear",
                        }}
                      />
                    ) : (
                      <path
                        d="M75% 58% L75% 78%"
                        stroke="currentColor"
                        className="stroke-border-secondary"
                        strokeWidth="2"
                        strokeDasharray="4 4"
                      />
                    )}
                    {activeAgent === "sentiment" ? (
                      <motion.path
                        d="M90% 58% L90% 78%"
                        stroke="currentColor"
                        className="stroke-teal-400 drop-shadow-[0_0_10px_rgba(45,212,191,0.95)]"
                        strokeWidth="2.5"
                        strokeDasharray="6 6"
                        animate={{ strokeDashoffset: [12, 0] }}
                        transition={{
                          repeat: Infinity,
                          duration: 1.1,
                          ease: "linear",
                        }}
                      />
                    ) : (
                      <path
                        d="M90% 58% L90% 78%"
                        stroke="currentColor"
                        className="stroke-border-secondary"
                        strokeWidth="2"
                        strokeDasharray="4 4"
                      />
                    )}
                  </svg>

                  <div className="w-full max-w-md">
                    <WorkflowCard
                      step={steps.find((s) => s.id === "supervisor")!}
                      isSelected={selectedAgent === "supervisor"}
                      isActive={activeAgent === "supervisor"}
                      onClick={() => setSelectedAgent("supervisor")}
                      label="Orchestrator"
                    />
                  </div>

                  <div className="grid w-full grid-cols-4 gap-4">
                    <WorkflowCard
                      step={steps.find((s) => s.id === "rag")!}
                      isSelected={selectedAgent === "rag"}
                      isActive={activeAgent === "rag"}
                      onClick={() => setSelectedAgent("rag")}
                      label="Context Retrieval"
                    />
                    <WorkflowCard
                      step={steps.find((s) => s.id === "financial")!}
                      isSelected={selectedAgent === "financial"}
                      isActive={activeAgent === "financial"}
                      onClick={() => setSelectedAgent("financial")}
                      label="Metrics & Ratios"
                    />
                    <WorkflowCard
                      step={steps.find((s) => s.id === "alert")!}
                      isSelected={selectedAgent === "alert"}
                      isActive={activeAgent === "alert"}
                      onClick={() => setSelectedAgent("alert")}
                      label="Risk Signals"
                    />
                    <WorkflowCard
                      step={steps.find((s) => s.id === "sentiment")!}
                      isSelected={selectedAgent === "sentiment"}
                      isActive={activeAgent === "sentiment"}
                      onClick={() => setSelectedAgent("sentiment")}
                      label="Market Sentiment"
                    />
                  </div>
                </div>
              </div>

              {/* Activity + logs */}
              <div className="grid grid-cols-1 gap-6 md:grid-cols-[1.1fr_1.9fr]">
                <div className="rounded-2xl border border-border-secondary bg-bg-tertiary/30 p-4">
                  <div className="mb-4 flex items-center gap-3">
                    <div
                      className={cn(
                        "flex h-10 w-10 items-center justify-center rounded-xl",
                        selectedAgent === "supervisor"
                          ? "bg-accent-primary/10 text-accent-primary"
                          : selectedAgent === "rag"
                            ? "bg-blue-500/10 text-blue-500"
                            : selectedAgent === "financial"
                              ? "bg-green-500/10 text-green-500"
                              : selectedAgent === "alert"
                                ? "bg-amber-500/10 text-amber-500"
                                : "bg-teal-500/10 text-teal-500",
                      )}
                    >
                      <currentStep.icon className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-text-primary">
                        {currentStep.name}
                      </h4>
                      <p className="text-xs text-text-tertiary">
                        {currentStep.description}
                      </p>
                    </div>
                  </div>
                  <div className="mb-3 flex items-center justify-between text-xs text-text-tertiary">
                    <span>Progress</span>
                    <span>{progressPercent}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-bg-primary">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all duration-700",
                        currentStep.status === "running" && "bg-accent-primary",
                        currentStep.status === "completed" && "bg-success",
                        currentStep.status === "skipped" && "bg-warning",
                        currentStep.status === "error" && "bg-error",
                        currentStep.status === "waiting" &&
                          "bg-border-secondary",
                      )}
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>

                <div className="h-[220px] overflow-hidden rounded-2xl border border-border-secondary bg-bg-tertiary font-mono text-xs">
                  <div className="flex items-center border-b border-border-secondary bg-bg-elevated px-4 py-2 text-text-tertiary">
                    <span className="mr-2 h-2 w-2 rounded-full bg-error"></span>
                    <span className="mr-2 h-2 w-2 rounded-full bg-warning"></span>
                    <span className="h-2 w-2 rounded-full bg-success"></span>
                    <span className="ml-4">live_activity.log</span>
                  </div>
                  <div className="h-full overflow-y-auto p-4 text-text-secondary">
                    {currentStep.logs.length > 0 ? (
                      currentStep.logs.map((log, i) => (
                        <div
                          key={i}
                          className="mb-1.5 border-l-2 border-border-secondary pl-2 opacity-80 hover:opacity-100"
                        >
                          <span className="mr-2 text-text-tertiary">
                            {log.split(" - ")[0]}
                          </span>
                          <span>{log.split(" - ")[1] || log}</span>
                        </div>
                      ))
                    ) : (
                      <div className="flex h-full items-center justify-center text-text-tertiary italic">
                        Waiting for agent activity...
                      </div>
                    )}
                    {currentStep.status === "running" && (
                      <div className="animate-pulse text-accent-primary">_</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function WorkflowCard({
  step,
  label,
  isSelected,
  isActive,
  onClick,
}: {
  step: AgentStep;
  label: string;
  isSelected: boolean;
  isActive?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "relative w-full rounded-2xl border bg-bg-elevated px-4 py-4 text-left transition-all",
        isSelected
          ? "border-accent-primary/60 shadow-[0_0_30px_-6px_rgba(var(--accent-primary),0.5)]"
          : "border-border-secondary",
        step.status === "running" && "ring-1 ring-accent-primary/40",
        step.status === "completed" && "border-success/30",
        step.status === "error" && "border-error/40",
        step.status === "skipped" && "border-warning/40",
        isActive &&
          step.id === "supervisor" &&
          "shadow-[0_0_40px_-4px_rgba(168,85,247,0.9)] border-fuchsia-400/50",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-xl",
              step.id === "supervisor"
                ? "bg-fuchsia-500/15 text-fuchsia-400"
                : step.id === "rag"
                  ? "bg-blue-500/15 text-blue-400"
                  : step.id === "financial"
                    ? "bg-emerald-500/15 text-emerald-400"
                    : step.id === "alert"
                      ? "bg-amber-500/15 text-amber-400"
                      : "bg-teal-500/15 text-teal-400",
            )}
          >
            <step.icon className="h-5 w-5" />
          </div>
          <div>
            <div className="text-sm font-semibold text-text-primary">
              {step.name}
            </div>
            <div className="text-xs text-text-tertiary">{label}</div>
          </div>
        </div>
        <span className="text-xs text-text-tertiary">
          {getProgressPercent(step.status)}%
        </span>
      </div>
      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-bg-primary">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-700",
            step.status === "running" && "bg-accent-primary",
            step.status === "completed" && "bg-success",
            step.status === "skipped" && "bg-warning",
            step.status === "error" && "bg-error",
            step.status === "waiting" && "bg-border-secondary",
          )}
          style={{ width: `${getProgressPercent(step.status)}%` }}
        />
      </div>
    </button>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "completed")
    return (
      <span className="rounded-full bg-success/10 px-2.5 py-1 text-xs font-medium text-success">
        Completed
      </span>
    );
  if (status === "running")
    return (
      <span className="rounded-full bg-accent-primary/10 px-2.5 py-1 text-xs font-medium text-accent-primary animate-pulse">
        Running
      </span>
    );
  if (status === "skipped")
    return (
      <span className="rounded-full bg-warning/10 px-2.5 py-1 text-xs font-medium text-warning">
        Skipped
      </span>
    );
  if (status === "error")
    return (
      <span className="rounded-full bg-error/10 px-2.5 py-1 text-xs font-medium text-error">
        Error
      </span>
    );
  return (
    <span className="rounded-full bg-bg-elevated px-2.5 py-1 text-xs font-medium text-text-tertiary">
      Waiting
    </span>
  );
}

function getProgressPercent(status: AgentStep["status"]) {
  if (status === "completed") return 100;
  if (status === "error") return 100;
  if (status === "skipped") return 0;
  if (status === "running") return 60;
  return 0;
}
