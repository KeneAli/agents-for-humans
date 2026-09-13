import { useState } from "react"
import { Check, ChevronDown, ChevronUp, FileText, Sparkles } from "lucide-react"

import type { AgentStatus } from "@/types/run"

export type ActivityState = "completed" | "current" | "pending" | "not-applicable"

export interface ActivityItem {
  id: string
  label: string
  activeLabel?: string
  state: ActivityState
  summary?: string
  live?: string[]
  evidence?: string[]
  agent_observation?: string
  timestamp?: string
}

interface AgentActivityProps {
  status: AgentStatus
  items: ActivityItem[]
}

function AgentActivity({ status, items }: AgentActivityProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const isAgentActive =
    status === "INVESTIGATING" ||
    status === "EXECUTING" ||
    status === "VERIFYING"

  return (
    <div className="border-t border-border px-5 py-4">
      <div className="flex items-center justify-between pb-3">
        <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Execution Trace
        </span>
        {isAgentActive && (
          <span className="flex items-center gap-1.5 text-xs text-emerald-500">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-60 duration-1000" />
              <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
            </span>
            <span className="text-[11px] font-medium">Active</span>
          </span>
        )}
      </div>

      <div className="space-y-3">
        {items.map((item) => {
          const isCurrent = item.state === "current"
          const isCompleted = item.state === "completed"
          const isPending = item.state === "pending"
          const isExpanded = expandedIds.has(item.id)
          const hasDetails = Boolean(
            (item.evidence && item.evidence.length > 0) || item.agent_observation,
          )

          return (
            <div
              key={item.id}
              className={`rounded-xl border transition-all duration-200 ${
                isCurrent
                  ? "border-border bg-muted/30 p-3 shadow-xs"
                  : isCompleted && hasDetails
                    ? "border-transparent bg-transparent hover:border-border/60 hover:bg-muted/20"
                    : "border-transparent bg-transparent"
              }`}
            >
              <div
                className={`flex items-start gap-3 text-xs ${
                  isCompleted && hasDetails ? "cursor-pointer select-none" : ""
                }`}
                onClick={() => {
                  if (isCompleted && hasDetails) {
                    toggleExpand(item.id)
                  }
                }}
              >
                {/* State Indicator */}
                {isCompleted ? (
                  <span className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-foreground text-background">
                    <Check className="size-2.5" strokeWidth={3} />
                  </span>
                ) : isCurrent ? (
                  <span className="relative mt-0.5 flex size-4 shrink-0 items-center justify-center">
                    <span className="absolute size-3.5 rounded-full bg-emerald-500/25 animate-pulse" />
                    <span className="relative size-2 rounded-full bg-emerald-500" />
                  </span>
                ) : item.state === "not-applicable" ? (
                  <span className="mt-0.5 flex size-4 shrink-0 items-center justify-center">
                    <span className="size-2 rounded-full bg-muted-foreground/20" />
                  </span>
                ) : (
                  <span className="mt-0.5 flex size-4 shrink-0 items-center justify-center">
                    <span className="size-2.5 rounded-full border border-border bg-background" />
                  </span>
                )}

                {/* Main Label and Summary */}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p
                      className={`leading-tight ${
                        isCurrent
                          ? "font-semibold text-foreground text-xs"
                          : isCompleted
                            ? "font-medium text-foreground"
                            : isPending
                              ? "text-muted-foreground/60"
                              : "text-muted-foreground/40"
                      }`}
                    >
                      {item.label}
                    </p>

                    <div className="flex items-center gap-1.5 shrink-0">
                      {item.timestamp && (
                        <span className="font-mono text-[10px] text-muted-foreground tabular-nums">
                          {new Date(item.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                          })}
                        </span>
                      )}

                      {isCompleted && hasDetails && (
                        <span className="text-muted-foreground/70">
                          {isExpanded ? (
                            <ChevronUp className="size-3" />
                          ) : (
                            <ChevronDown className="size-3" />
                          )}
                        </span>
                      )}
                    </div>
                  </div>

                  {item.summary && (
                    <p
                      className={`mt-1 text-[11px] leading-relaxed ${
                        isCurrent ? "text-foreground/90 font-normal" : "text-muted-foreground"
                      }`}
                    >
                      {item.summary}
                    </p>
                  )}

                  {/* Active Live Incremental Activity */}
                  {isCurrent && item.live && item.live.length > 0 && (
                    <div className="mt-2.5 rounded-lg border border-border/80 bg-background/90 p-2.5 text-[11px] space-y-1.5">
                      <div className="flex items-center gap-1.5 font-medium text-foreground text-[10px] uppercase tracking-wider">
                        <Sparkles className="size-3 text-emerald-500" />
                        Live agent activity
                      </div>
                      <div className="space-y-1 text-muted-foreground">
                        {item.live.map((step, idx) => (
                          <div key={`live-${item.id}-${idx}`} className="flex items-center gap-2">
                            <span className="size-1 rounded-full bg-emerald-500/80" />
                            <span>{step}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Expanded Evidence & Agent Observation for Completed Items */}
                  {isCompleted && isExpanded && (
                    <div className="mt-3 space-y-3 rounded-lg border border-border/60 bg-muted/20 p-3">
                      {/* Structured Evidence */}
                      {item.evidence && item.evidence.length > 0 && (
                        <div>
                          <div className="flex items-center gap-1.5 font-semibold text-[10px] uppercase tracking-wider text-muted-foreground">
                            <FileText className="size-3" />
                            Evidence
                          </div>
                          <ul className="mt-1.5 space-y-1 text-[11px] text-foreground/90">
                            {item.evidence.map((evidenceItem, idx) => (
                              <li key={`ev-${item.id}-${idx}`} className="flex items-start gap-1.5">
                                <span className="text-muted-foreground">•</span>
                                <span className="leading-tight">{evidenceItem}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Agent Observation */}
                      {item.agent_observation && (
                        <div className="rounded-lg border border-border/80 bg-card p-2.5 shadow-2xs">
                          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                            Agent observation
                          </div>
                          <p className="mt-1 text-[11px] leading-relaxed text-foreground font-normal">
                            {item.agent_observation}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default AgentActivity
