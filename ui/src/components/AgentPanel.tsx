import {
  CheckCircle2,
  CircleDot,
  Clock,
  LoaderCircle,
  ShieldCheck,
  TriangleAlert,
  UserRound,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import AgentActivity, { type ActivityItem } from "@/components/AgentActivity"

import type { AgentStatus } from "@/types/run"

interface AgentPanelProps {
  status: AgentStatus
  activity: ActivityItem[]
  onOpenApproval?: () => void
}

function AgentPanel({
  status,
  activity,
  onOpenApproval,
}: AgentPanelProps) {
  const panelContent = {
    MONITORING: {
      icon: CircleDot,
      title: "SCÉANCE Activity",
      subtitle: "Monitoring",
      description:
        "SCÉANCE is actively monitoring the network for disruptions.",
    },

    INVESTIGATING: {
      icon: LoaderCircle,
      title: "SCÉANCE Activity",
      subtitle: "Investigation in progress",
      description:
        "SCÉANCE is analyzing shipment context, delay consequences, and recovery options.",
    },

    AWAITING_APPROVAL: {
      icon: TriangleAlert,
      title: "SCÉANCE Activity",
      subtitle: "Approval required",
      description:
        "SCÉANCE evaluated recovery options and is waiting for human authorization.",
    },

    EXECUTING: {
      icon: LoaderCircle,
      title: "SCÉANCE Activity",
      subtitle: "Recovery in progress",
      description:
        "Authorization received. SCÉANCE is executing the approved recovery action.",
    },

    VERIFYING: {
      icon: ShieldCheck,
      title: "SCÉANCE Activity",
      subtitle: "Verifying state",
      description:
        "SCÉANCE is verifying the resulting operational state in the supply chain.",
    },

    RESOLVED: {
      icon: CheckCircle2,
      title: "SCÉANCE Activity",
      subtitle: "Recovery verified",
      description:
        "The recovery workflow completed and operational state has been verified.",
    },

    NO_ACTION: {
      icon: CheckCircle2,
      title: "SCÉANCE Activity",
      subtitle: "No action required",
      description:
        "SCÉANCE investigated the disruption and determined that no recovery action is required.",
    },

    REJECTED: {
      icon: TriangleAlert,
      title: "SCÉANCE Activity",
      subtitle: "Recommendation rejected",
      description:
        "The operator declined the proposed recovery action. No recovery workflow was executed.",
    },
  } satisfies Record<
    AgentStatus,
    {
      icon: typeof CircleDot
      title: string
      subtitle: string
      description: string
    }
  >

  const content = panelContent[status]
  const Icon = content.icon

  const isProcessing =
    status === "INVESTIGATING" ||
    status === "EXECUTING" ||
    status === "VERIFYING"

  return (
    <div className="rounded-2xl border border-border bg-card">
      <div className="border-b border-border px-6 py-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="font-medium">{content.title}</h2>
          </div>

          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${
              status === "RESOLVED"
                ? "bg-emerald-500/10 text-emerald-500"
                : status === "AWAITING_APPROVAL"
                  ? "bg-amber-500/10 text-amber-500"
                  : status === "REJECTED"
                    ? "bg-destructive/10 text-destructive"
                    : "bg-muted text-muted-foreground"
            }`}
          >
            <Icon
              className={`size-3 ${
                isProcessing ? "animate-spin text-foreground" : ""
              }`}
            />
            <span>{content.subtitle}</span>
          </span>
        </div>

        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {content.description}
        </p>
      </div>

      {status === "AWAITING_APPROVAL" && (
        <div className="space-y-4 border-b border-border bg-amber-500/5 px-6 py-5">
          <div className="flex items-start gap-3 rounded-xl border border-amber-500/20 bg-background/80 p-3.5">
            <ShieldCheck className="mt-0.5 size-4 shrink-0 text-amber-500" />
            <div className="text-xs leading-relaxed text-muted-foreground">
              <strong className="font-semibold text-foreground">Human Authorization Required:</strong>{" "}
              The agent cannot execute this recovery without explicit operator approval.
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <Clock className="size-3.5" />
              Approval window active
            </span>
          </div>

          <Button className="w-full" onClick={onOpenApproval}>
            <UserRound className="size-4" />
            Review recommendation
          </Button>
        </div>
      )}

      <AgentActivity status={status} items={activity} />

      {status === "INVESTIGATING" && (
        <div className="border-t border-border/60 px-6 py-4">
          <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Current activity
          </p>
          <p className="mt-1 text-xs text-foreground">
            Evaluating shipment context and recovery constraints…
          </p>
        </div>
      )}

      {status === "EXECUTING" && (
        <div className="border-t border-border/60 px-6 py-4">
          <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Current activity
          </p>
          <p className="mt-1 text-xs text-foreground">
            Executing the selected recovery workflow…
          </p>
        </div>
      )}

      {status === "VERIFYING" && (
        <div className="border-t border-border/60 px-6 py-4">
          <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Current activity
          </p>
          <p className="mt-1 text-xs text-foreground">
            Checking the shipment's resulting operational state…
          </p>
        </div>
      )}
    </div>
  )
}

export default AgentPanel