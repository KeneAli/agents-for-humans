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

import type { AgentStatus } from "@/types/run"

interface AgentPanelProps {
  status: AgentStatus
}

function AgentPanel({ status }: AgentPanelProps) {
  const panelContent = {
    MONITORING: {
      icon: CircleDot,
      title: "Monitoring",
      description:
        "SCÉANCE is monitoring the shipment for changes that may require attention.",
    },

    INVESTIGATING: {
      icon: LoaderCircle,
      title: "Investigation in progress",
      description:
        "SCÉANCE is reviewing the shipment context, disruption details and available recovery options.",
    },

    AWAITING_APPROVAL: {
      icon: TriangleAlert,
      title: "Approval required",
      description:
        "SCÉANCE has found a recovery option and is waiting for a human decision.",
    },

    EXECUTING: {
      icon: LoaderCircle,
      title: "Recovery in progress",
      description:
        "Approval has been received. SCÉANCE is executing the selected recovery workflow.",
    },

    VERIFYING: {
      icon: ShieldCheck,
      title: "Verifying recovery",
      description:
        "SCÉANCE is checking the resulting operational state to confirm that the recovery succeeded.",
    },

    RESOLVED: {
      icon: CheckCircle2,
      title: "Recovery verified",
      description:
        "The recovery workflow completed successfully and the resulting operational state has been verified.",
    },

    NO_ACTION: {
      icon: CheckCircle2,
      title: "No action required",
      description:
        "SCÉANCE investigated the disruption and determined that no recovery action is required.",
    },
  } satisfies Record<
    AgentStatus,
    {
      icon: typeof CircleDot
      title: string
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
        <div className="flex items-center gap-2">
          <Icon
            className={`size-4 ${
              isProcessing ? "animate-spin" : ""
            }`}
          />

          <h2 className="font-medium">{content.title}</h2>
        </div>

        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {content.description}
        </p>
      </div>

      {status === "AWAITING_APPROVAL" && (
        <div className="space-y-5 px-6 py-6">
          <div>
            <p className="text-xs text-muted-foreground">
              Recommended action
            </p>

            <p className="mt-2 text-sm font-medium">
              Execute selected recovery workflow
            </p>
          </div>

          <div className="flex items-start gap-3 rounded-xl bg-muted/50 p-4">
            <ShieldCheck className="mt-0.5 size-4 shrink-0 text-muted-foreground" />

            <p className="text-xs leading-5 text-muted-foreground">
              The agent cannot execute this recovery without
              explicit operator approval.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="size-3.5" />
            Approval window is active
          </div>

          <Button className="w-full">
            <UserRound className="size-4" />
            Approve recovery
          </Button>

          <Button variant="outline" className="w-full">
            Reject
          </Button>
        </div>
      )}

      {status === "INVESTIGATING" && (
        <div className="px-6 py-6">
          <p className="text-xs text-muted-foreground">
            Current activity
          </p>

          <p className="mt-2 text-sm">
            Evaluating shipment context and recovery constraints…
          </p>
        </div>
      )}

      {status === "EXECUTING" && (
        <div className="px-6 py-6">
          <p className="text-xs text-muted-foreground">
            Current activity
          </p>

          <p className="mt-2 text-sm">
            Executing the selected recovery workflow…
          </p>
        </div>
      )}

      {status === "VERIFYING" && (
        <div className="px-6 py-6">
          <p className="text-xs text-muted-foreground">
            Current activity
          </p>

          <p className="mt-2 text-sm">
            Checking the shipment's resulting operational state…
          </p>
        </div>
      )}

      {status === "RESOLVED" && (
        <div className="px-6 py-6">
          <div className="rounded-xl bg-muted/50 p-4">
            <p className="text-xs text-muted-foreground">
              Outcome
            </p>

            <p className="mt-2 text-sm font-medium">
              Shipment recovered
            </p>
          </div>
        </div>
      )}

      {status === "NO_ACTION" && (
        <div className="px-6 py-6">
          <div className="rounded-xl bg-muted/50 p-4">
            <p className="text-xs text-muted-foreground">
              Outcome
            </p>

            <p className="mt-2 text-sm font-medium">
              No recovery action required
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default AgentPanel