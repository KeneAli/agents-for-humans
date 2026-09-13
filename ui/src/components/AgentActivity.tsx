import { Check } from "lucide-react"

import type { AgentStatus } from "@/types/run"

export type ActivityState = "completed" | "current" | "pending" | "not-applicable"

export interface ActivityItem {
  label: string
  state: ActivityState
  description?: string
  timestamp?: string
}

interface AgentActivityProps {
  status: AgentStatus
  items: ActivityItem[]
}

function AgentActivity({ status, items }: AgentActivityProps) {
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

          return (
            <div
              key={item.label}
              className={`flex items-start gap-3 text-xs transition-colors duration-200 ${
                isCompleted
                  ? "text-foreground"
                  : isCurrent
                    ? "text-foreground font-medium"
                    : isPending
                      ? "text-muted-foreground/60"
                      : "text-muted-foreground/40"
              }`}
            >
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

              <div className="min-w-0 flex-1">
                <p className={isCurrent ? "font-semibold text-foreground text-xs" : "leading-normal text-xs"}>
                  {item.label}
                </p>
                {item.description && (
                  <p className="mt-0.5 text-[11px] leading-tight text-muted-foreground">
                    {item.description}
                  </p>
                )}
              </div>

              {item.timestamp && (
                <span className="shrink-0 font-mono text-[10px] text-muted-foreground tabular-nums">
                  {new Date(item.timestamp).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })}
                </span>
              )}

              {item.state === "not-applicable" && (
                <span className="shrink-0 text-[10px] text-muted-foreground">Not required</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default AgentActivity
