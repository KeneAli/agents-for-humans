import { Check, Circle } from "lucide-react"

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
  const hasCurrentActivity = items.some((item) => item.state === "current")

  return (
    <div className="border-t border-border px-6 py-5">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
        SCÉANCE activity
      </p>

      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <div
            key={item.label}
            className={`flex items-center gap-3 text-sm transition-opacity duration-200 ${
              item.state === "pending" || item.state === "not-applicable"
                ? "text-muted-foreground"
                : "text-foreground"
            }`}
          >
            {item.state === "completed" ? (
              <span className="flex size-4 items-center justify-center rounded-full bg-foreground text-background">
                <Check className="size-2.5" strokeWidth={3} />
              </span>
            ) : item.state === "current" ? (
              <span className="relative flex size-4 items-center justify-center">
                <span className="size-3 rounded-full border-2 border-foreground" />
                {hasCurrentActivity && status !== "AWAITING_APPROVAL" && (
                  <span className="absolute size-1.5 rounded-full bg-foreground animate-pulse" />
                )}
              </span>
            ) : (
              <Circle className="size-3 text-border" />
            )}

            <div>
              <p>{item.label}</p>
              {item.description && (
                <p className="mt-0.5 text-xs leading-5 text-muted-foreground">
                  {item.description}
                </p>
              )}
            </div>
            {item.timestamp && (
              <span className="ml-auto text-xs text-muted-foreground">
                {new Date(item.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </span>
            )}
            {item.state === "not-applicable" && (
              <span className="ml-auto text-xs">Not required</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default AgentActivity
