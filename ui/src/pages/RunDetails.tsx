import {
  ArrowLeft,
  Check,
  Circle,
} from "lucide-react"

import { Link, useParams } from "react-router"

import AgentPanel from "@/components/AgentPanel"
import { useSimulation } from "@/context/SimulationContext"
import type { AgentStatus } from "@/types/run"

function RunDetails() {
  const { shipmentId, runId } = useParams()
  const { getRun } = useSimulation()

  const run =
  shipmentId && runId
    ? getRun(shipmentId, runId)
    : undefined

  

  if (!run) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8">
        Run not found.
      </div>
    )
  }

  const agentStatus = run.agentStatus

  const statusProgress: Record<AgentStatus, number> = {
    MONITORING: 0,
    INVESTIGATING: 1,
    AWAITING_APPROVAL: 3,
    EXECUTING: 4,
    VERIFYING: 5,
    RESOLVED: 6,
    NO_ACTION: 6,
  }

  const disruptionLabel = run.disruption?.type
    ? run.disruption.type
        .replaceAll("_", " ")
        .toLowerCase()
        .replace(/^./, (char) => char.toUpperCase())
    : "Operational disruption"

  const timeline = [
    {
      key: "DISRUPTION_DETECTED",
      title: "Disruption detected",
      description: `${disruptionLabel} reported on the ${run.route} route.`,
      time: "18:02",
    },
    {
      key: "INVESTIGATING",
      title: "Agent investigated",
      description:
        "SCÉANCE evaluated the shipment context and available recovery options.",
      time: "18:03",
    },
    {
      key: "RECOMMENDATION",
      title: "Recovery recommended",
      description:
        "A recovery option was selected based on the operational constraints.",
      time: "18:03",
    },
    {
      key: "AWAITING_APPROVAL",
      title: "Human approval",
      description:
        "The recommended recovery requires operator approval before execution.",
      time: "Now",
    },
    {
      key: "EXECUTING",
      title: "Recovery execution",
      description:
        "Execution will begin after approval.",
      time: "",
    },
    {
      key: "VERIFYING",
      title: "Verification",
      description:
        "SCÉANCE will verify the resulting operational state.",
      time: "",
    },
    {
      key: "RESOLVED",
      title: "Resolved",
      description:
        "The recovery has completed and the resulting operational state has been verified.",
      time: "",
    },
  ]

  const currentProgress = statusProgress[agentStatus]

  return (
    <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8">
      <Link
        to="/"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" />
        Operations
      </Link>

      <header className="mt-8">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm text-muted-foreground">
            Recovery run
          </span>

          <span className="text-border">/</span>

          <span className="font-medium">{run.shipmentId}</span>
        </div>

        <div className="mt-5 flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-4xl font-semibold tracking-tight">
                {disruptionLabel}
              </h1>

              <span className="inline-flex items-center gap-2 rounded-full border border-border bg-muted/40 px-3 py-1 text-xs font-medium">
                <Circle className="size-2 fill-current" />

                {agentStatus
                  .replaceAll("_", " ")
                  .toLowerCase()
                  .replace(/^./, (char) => char.toUpperCase())}
              </span>
            </div>

            <p className="mt-3 text-base text-muted-foreground">
              {run.route}
              {run.disruption?.durationMinutes
                ? ` · disruption duration ${run.disruption.durationMinutes} min`
                : ""}
            </p>
          </div>

          <div className="text-sm text-muted-foreground">
            Run ID

            <div className="mt-1 font-mono text-xs text-foreground">
              {run.runId}
            </div>
          </div>
        </div>
      </header>

      <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_360px]">
        <section>
          <div className="rounded-2xl border border-border bg-card">
            <div className="border-b border-border px-6 py-5">
              <h2 className="font-medium">Recovery timeline</h2>

              <p className="mt-1 text-sm text-muted-foreground">
                What SCÉANCE has done and what happens next.
              </p>
            </div>

            <div className="px-6 py-7">
              {timeline.map((event, index) => {
                const isComplete = index < currentProgress
                const isCurrent = index === currentProgress
                const isLast = index === timeline.length - 1

                return (
                  <div
                    key={event.key}
                    className="relative flex gap-4"
                  >
                    {!isLast && (
                      <div
                        className={`absolute left-[7px] top-5 h-full w-px ${
                          isComplete
                            ? "bg-foreground/20"
                            : "bg-border"
                        }`}
                      />
                    )}

                    <div className="relative z-10 flex size-4 shrink-0 items-center justify-center">
                      {isComplete ? (
                        <div className="flex size-4 items-center justify-center rounded-full bg-foreground text-background">
                          <Check
                            className="size-2.5"
                            strokeWidth={3}
                          />
                        </div>
                      ) : isCurrent ? (
                        <div className="flex size-4 items-center justify-center rounded-full border-2 border-foreground bg-background">
                          <div className="size-1.5 rounded-full bg-foreground" />
                        </div>
                      ) : (
                        <div className="size-3 rounded-full border border-border bg-background" />
                      )}
                    </div>

                    <div className="pb-9">
                      <div className="flex items-center gap-3">
                        <h3
                          className={`text-sm font-medium ${
                            !isComplete && !isCurrent
                              ? "text-muted-foreground"
                              : ""
                          }`}
                        >
                          {event.title}
                        </h3>

                        {event.time && (
                          <span className="text-xs text-muted-foreground">
                            {event.time}
                          </span>
                        )}
                      </div>

                      <p className="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">
                        {event.description}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        <aside>
          <AgentPanel status={agentStatus} />
        </aside>
      </div>
    </div>
  )
}

export default RunDetails