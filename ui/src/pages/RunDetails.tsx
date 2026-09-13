import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ArrowLeft, Check, Circle } from "lucide-react"
import { Link, useParams } from "react-router"

import AgentPanel from "@/components/AgentPanel"
import type { ActivityItem } from "@/components/AgentActivity"
import RecoveryApprovalDialog from "@/components/RecoveryApprovalDialog"
import RunOutcomeSummary from "@/components/RunOutcomeSummary"
import { useRun } from "@/hooks/useRun"
import { useShipments } from "@/hooks/useShipments"
import { submitDecision } from "@/lib/api"
import type { AgentStatus } from "@/types/run"

type TimelineState = "completed" | "current" | "pending" | "not-applicable"

const timelineSequence = [
  {
    key: "OPTIONS_EVALUATED",
    title: "Agent investigated",
    description: "Shipment context and recovery options were evaluated.",
  },
  {
    key: "RECOVERY_SELECTED",
    title: "Recovery recommended",
    description: "The best available recovery option was selected.",
  },
  {
    key: "APPROVAL_GRANTED",
    title: "Human decision",
    description: "The recommended recovery is awaiting an operator decision.",
  },
  {
    key: "RECOVERY_EXECUTED",
    title: "Recovery execution",
    description: "The authorized recovery action will execute after approval.",
  },
  {
    key: "STATE_VERIFIED",
    title: "Verification",
    description: "The resulting shipment state will be verified after execution.",
  },
  {
    key: "RESOLVED",
    title: "Resolved",
    description: "The recovery workflow completes after verification.",
  },
]

function label(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/^./, (character) => character.toUpperCase())
}

function toAgentStatus(workflowStatus?: string, approvalStatus?: string, action?: string | null): AgentStatus {
  if (approvalStatus === "REJECTED" || workflowStatus === "REJECTED") return "REJECTED"
  if (action === "DO_NOTHING") return "NO_ACTION"
  if (workflowStatus === "COMPLETED") return "RESOLVED"
  if (workflowStatus === "FAILED" || approvalStatus === "EXPIRED") return "NO_ACTION"
  if (workflowStatus === "PENDING_APPROVAL" || approvalStatus === "PENDING_APPROVAL") return "AWAITING_APPROVAL"
  if (workflowStatus === "EXECUTING" || approvalStatus === "APPROVAL_IN_PROGRESS") return "EXECUTING"
  return "INVESTIGATING"
}

function getActiveTimelineKey(auditKeys: Set<string>, agentStatus: AgentStatus): string | null {
  if (agentStatus === "RESOLVED" || agentStatus === "REJECTED" || agentStatus === "NO_ACTION") {
    return null
  }
  if (!auditKeys.has("OPTIONS_EVALUATED")) return "OPTIONS_EVALUATED"
  if (!auditKeys.has("RECOVERY_SELECTED")) return "RECOVERY_SELECTED"
  if (agentStatus === "AWAITING_APPROVAL" || !auditKeys.has("APPROVAL_GRANTED")) return "APPROVAL_GRANTED"
  if (agentStatus === "EXECUTING" || !auditKeys.has("RECOVERY_EXECUTED")) return "RECOVERY_EXECUTED"
  if (!auditKeys.has("STATE_VERIFIED")) return "STATE_VERIFIED"
  return "RESOLVED"
}

function stateForStep(
  stepKey: string,
  hasAudit: boolean,
  auditKeys: Set<string>,
  agentStatus: AgentStatus,
): TimelineState {
  if (agentStatus === "RESOLVED") {
    return "completed"
  }
  if (agentStatus === "REJECTED") {
    if (["OPTIONS_EVALUATED", "RECOVERY_SELECTED", "APPROVAL_GRANTED", "RESOLVED"].includes(stepKey)) {
      return "completed"
    }
    return "not-applicable"
  }
  if (agentStatus === "NO_ACTION") {
    if (["OPTIONS_EVALUATED", "RECOVERY_SELECTED", "RESOLVED"].includes(stepKey)) {
      return "completed"
    }
    return "not-applicable"
  }

  const activeKey = getActiveTimelineKey(auditKeys, agentStatus)
  if (stepKey === activeKey) return "current"

  const stepOrder = ["OPTIONS_EVALUATED", "RECOVERY_SELECTED", "APPROVAL_GRANTED", "RECOVERY_EXECUTED", "STATE_VERIFIED", "RESOLVED"]
  const activeIndex = activeKey ? stepOrder.indexOf(activeKey) : -1
  const thisIndex = stepOrder.indexOf(stepKey)

  if (hasAudit || (activeIndex !== -1 && thisIndex < activeIndex)) {
    return "completed"
  }
  return "pending"
}

function extractEvidence(event?: { details: Record<string, unknown> }): string[] | undefined {
  if (!event?.details) return undefined
  if (Array.isArray(event.details.details) && event.details.details.every((item) => typeof item === "string")) {
    return event.details.details as string[]
  }
  return undefined
}

function extractLive(event?: { details: Record<string, unknown> }): string[] | undefined {
  if (!event?.details) return undefined
  if (Array.isArray(event.details.live) && event.details.live.every((item) => typeof item === "string")) {
    return event.details.live as string[]
  }
  return undefined
}

function extractObservation(event?: { details: Record<string, unknown> }): string | undefined {
  if (!event?.details) return undefined
  if (typeof event.details.agent_observation === "string" && event.details.agent_observation.trim()) {
    return event.details.agent_observation.trim()
  }
  return undefined
}

function extractSummary(event?: { details: Record<string, unknown> }, fallback?: string): string | undefined {
  if (event?.details && typeof event.details.summary === "string" && event.details.summary.trim()) {
    return event.details.summary.trim()
  }
  return fallback
}

function activityForRun(
  agentStatus: AgentStatus,
  auditEvents: Array<{ event_type: string; timestamp: string; details: Record<string, unknown> }>,
): ActivityItem[] {
  const byType = new Map(auditEvents.map((event) => [event.event_type, event]))
  const auditKeys = new Set(byType.keys())

  const traceDefinitions = [
    {
      key: "CONTEXT",
      startedEvent: "SHIPMENT_CONTEXT_REVIEW_STARTED",
      completedEvent: "SHIPMENT_CONTEXT_REVIEWED",
      completedLabel: "Shipment context reviewed",
      activeLabel: "Reviewing shipment context",
      description: "Checking current shipment status and delivery window.",
    },
    {
      key: "IMPACT",
      startedEvent: "DELAY_IMPACT_ASSESSMENT_STARTED",
      completedEvent: "DELAY_IMPACT_ASSESSED",
      completedLabel: "Delay impact assessed",
      activeLabel: "Assessing delay impact",
      description: "Calculating expected impact on delivery.",
    },
    {
      key: "OPTIONS",
      startedEvent: "RECOVERY_OPTIONS_EVALUATION_STARTED",
      completedEvent: "OPTIONS_EVALUATED",
      completedLabel: "Recovery options evaluated",
      activeLabel: "Evaluating recovery options",
      description: "Comparing available recovery strategies.",
    },
    {
      key: "RECOMMENDATION",
      startedEvent: null,
      completedEvent: "RECOMMENDATION_PREPARED",
      completedLabel: "Recovery recommendation prepared",
      activeLabel: "Preparing recommendation",
      description: "Preparing selected action for operator review.",
    },
    {
      key: "APPROVAL",
      startedEvent: null,
      completedEvent: "APPROVAL_REQUESTED",
      completedLabel: "Awaiting operator approval",
      activeLabel: "Awaiting operator approval",
      description: "Waiting for operator authorization.",
    },
    {
      key: "EXECUTION",
      startedEvent: "RECOVERY_EXECUTION_STARTED",
      completedEvent: "RECOVERY_EXECUTED",
      completedLabel: "Recovery executed",
      activeLabel: "Executing recovery action",
      description: "Applying the authorized recovery action.",
    },
    {
      key: "VERIFICATION",
      startedEvent: "VERIFICATION_STARTED",
      completedEvent: "VERIFICATION_COMPLETED",
      completedLabel: "Shipment state verified",
      activeLabel: "Verifying shipment state",
      description: "Checking resulting operational state.",
    },
  ]

  // Terminal scenarios
  if (agentStatus === "REJECTED") {
    const items: ActivityItem[] = []
    for (const def of traceDefinitions.slice(0, 4)) {
      const completed = byType.get(def.completedEvent)
      items.push({
        id: def.key,
        label: def.completedLabel,
        summary: extractSummary(completed, def.description),
        evidence: extractEvidence(completed),
        agent_observation: extractObservation(completed),
        state: "completed",
        timestamp: completed?.timestamp,
      })
    }
    const rejectAudit = byType.get("RECOVERY_REJECTED") ?? byType.get("APPROVAL_REQUESTED")
    items.push({
      id: "REJECTION",
      label: "Operator declined recommendation",
      summary: extractSummary(rejectAudit, "Recovery execution was bypassed per human override."),
      evidence: extractEvidence(rejectAudit) ?? ["Operator Decision: REJECTED", "Execution: Bypassed per human override"],
      agent_observation: extractObservation(rejectAudit) ?? "The operator declined the proposed recovery action. Execution bypassed; shipment remains on unmitigated trajectory.",
      state: "completed",
      timestamp: rejectAudit?.timestamp,
    })
    return items
  }

  if (agentStatus === "NO_ACTION") {
    const items: ActivityItem[] = []
    for (const def of traceDefinitions.slice(0, 4)) {
      const completed = byType.get(def.completedEvent)
      items.push({
        id: def.key,
        label: def.completedLabel,
        summary: extractSummary(completed, def.description),
        evidence: extractEvidence(completed),
        agent_observation: extractObservation(completed),
        state: "completed",
        timestamp: completed?.timestamp,
      })
    }
    const noActionAudit = byType.get("RECOMMENDATION_PREPARED") ?? byType.get("OPTIONS_EVALUATED")
    items.push({
      id: "NO_ACTION",
      label: "No recovery required",
      summary: "Disruption delay is within SLA tolerance with zero penalty exposure.",
      evidence: ["Delay is within contract SLA tolerance", "Zero financial penalty exposure"],
      agent_observation: "SCÉANCE determined that no recovery action is required because delivery commitments remain intact.",
      state: "completed",
      timestamp: noActionAudit?.timestamp,
    })
    return items
  }

  if (agentStatus === "RESOLVED") {
    const items: ActivityItem[] = []
    for (const def of traceDefinitions) {
      const completed = byType.get(def.completedEvent)
      items.push({
        id: def.key,
        label: def.completedLabel,
        summary: extractSummary(completed, def.description),
        evidence: extractEvidence(completed),
        agent_observation: extractObservation(completed),
        state: "completed",
        timestamp: completed?.timestamp,
      })
    }
    return items
  }

  // Active / in-progress run
  let activeIndex = 0
  if (!auditKeys.has("SHIPMENT_CONTEXT_REVIEWED")) {
    activeIndex = 0
  } else if (!auditKeys.has("DELAY_IMPACT_ASSESSED")) {
    activeIndex = 1
  } else if (!auditKeys.has("OPTIONS_EVALUATED")) {
    activeIndex = 2
  } else if (!auditKeys.has("RECOMMENDATION_PREPARED")) {
    activeIndex = 3
  } else if (agentStatus === "AWAITING_APPROVAL" || !auditKeys.has("APPROVAL_GRANTED")) {
    activeIndex = 4
  } else if (!auditKeys.has("RECOVERY_EXECUTED")) {
    activeIndex = 5
  } else if (!auditKeys.has("VERIFICATION_COMPLETED") && !auditKeys.has("STATE_VERIFIED")) {
    activeIndex = 6
  } else {
    activeIndex = 7
  }

  const items: ActivityItem[] = []
  traceDefinitions.forEach((def, index) => {
    if (index < activeIndex) {
      const completed = byType.get(def.completedEvent)
      items.push({
        id: def.key,
        label: def.completedLabel,
        summary: extractSummary(completed, def.description),
        evidence: extractEvidence(completed),
        agent_observation: extractObservation(completed),
        state: "completed",
        timestamp: completed?.timestamp,
      })
    } else if (index === activeIndex) {
      const started = def.startedEvent ? byType.get(def.startedEvent) : undefined
      items.push({
        id: def.key,
        label: def.activeLabel,
        summary: extractSummary(started, def.description),
        live: extractLive(started),
        state: "current",
        timestamp: started?.timestamp,
      })
    } else {
      items.push({
        id: def.key,
        label: def.completedLabel,
        summary: def.description,
        state: "pending",
      })
    }
  })

  return items
}

function numberFromDetails(value: unknown): number | undefined {
  return typeof value === "number" ? value : undefined
}

function RunDetails() {
  const { shipmentId, runId } = useParams()
  const queryClient = useQueryClient()
  const runQuery = useRun(shipmentId, runId)
  const shipmentsQuery = useShipments()
  const [dismissedApprovalRunId, setDismissedApprovalRunId] = useState<string>()
  const decisionMutation = useMutation({
    mutationFn: (decision: "approve" | "reject") => submitDecision(shipmentId!, runId!, decision),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["run", shipmentId, runId] }),
  })
  const pendingAction = runQuery.data?.workflow?.action ?? runQuery.data?.approval?.option_type
  const approvalRequired =
    pendingAction !== "DO_NOTHING"
    && (
      runQuery.data?.workflow?.status === "PENDING_APPROVAL"
      || runQuery.data?.approval?.status === "PENDING_APPROVAL"
    )

  const approvalOpen = approvalRequired && dismissedApprovalRunId !== runId

  if (!shipmentId || !runId) {
    return <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8">Run not found.</div>
  }

  const run = runQuery.data
  const shipment = shipmentsQuery.data?.shipments.find((item) => item.shipment_id === shipmentId)
  const action = run?.workflow?.action ?? run?.approval?.option_type
  const agentStatus = run
    ? toAgentStatus(run.workflow?.status, run.approval?.status, action)
    : "INVESTIGATING"
  const auditEvents = run?.audit_events ?? []
  const auditByType = new Map(auditEvents.map((event) => [event.event_type, event]))
  const auditKeys = new Set(auditByType.keys())
  const activity = run
    ? activityForRun(agentStatus, auditEvents)
    : [
        {
          id: "CONTEXT",
          label: "Reviewing shipment context",
          activeLabel: "Reviewing shipment context",
          summary: "Checking current shipment status and delivery window.",
          live: [
            "Retrieving shipment record and operational status...",
            "Checking route origin, destination, and distance...",
            "Verifying carrier profile and transit requirements...",
          ],
          state: "current" as const,
        },
      ]

  const optionsAudit = auditByType.get("OPTIONS_EVALUATED")
  const executionAudit = auditByType.get("RECOVERY_EXECUTED")
  const verificationAudit = auditByType.get("STATE_VERIFIED")
  const projectedPenalty =
    numberFromDetails(optionsAudit?.details.projected_sla_penalty_eur) ??
    run?.approval?.projected_sla_penalty_eur ??
    undefined
  const recoveryCost = numberFromDetails(executionAudit?.details.recovery_cost_eur)
  const estimatedRecoveryHours =
    numberFromDetails(executionAudit?.details.estimated_recovery_hours) ??
    run?.approval?.estimated_recovery_hours ??
    undefined
  const netBenefit = numberFromDetails(optionsAudit?.details.net_benefit_eur)
  const delayMinutes =
    numberFromDetails(run?.approval?.current_delay_minutes) ??
    numberFromDetails(optionsAudit?.details.delay_minutes) ??
    undefined
  const verifiedEta =
    typeof verificationAudit?.details.current_eta === "string"
      ? verificationAudit.details.current_eta
      : undefined

  const timeline = [
    {
      key: "DISRUPTION_DETECTED",
      title: "Disruption detected",
      description: "The operational disruption was submitted for investigation.",
      state: "completed" as TimelineState,
      time: run?.approval?.created_at ?? run?.workflow?.event_id,
    },
    ...timelineSequence.map((step) => {
      const audit = auditByType.get(step.key)
      const state = run
        ? stateForStep(step.key, Boolean(audit), auditKeys, agentStatus)
        : step.key === "OPTIONS_EVALUATED"
          ? ("current" as TimelineState)
          : ("pending" as TimelineState)
      const description =
        audit && step.key === "RECOVERY_EXECUTED"
          ? "The authorized recovery action was executed."
          : audit && step.key === "STATE_VERIFIED"
            ? "The resulting shipment state was verified."
            : audit && step.key === "RESOLVED"
              ? "The recovery workflow completed successfully."
              : audit && step.key === "APPROVAL_GRANTED"
                ? "The operator approved the proposed recovery action."
                : agentStatus === "REJECTED" && step.key === "APPROVAL_GRANTED"
                  ? "The operator declined the proposed recovery action."
                  : agentStatus === "REJECTED" && step.key === "RECOVERY_EXECUTED"
                    ? "Not executed because the operator rejected the recommendation."
                    : agentStatus === "REJECTED" && step.key === "STATE_VERIFIED"
                      ? "Not required because recovery was not executed."
                      : agentStatus === "NO_ACTION" && step.key === "RECOVERY_SELECTED"
                        ? "SCÉANCE determined that no recovery action is required."
                        : agentStatus === "NO_ACTION" && step.key === "APPROVAL_GRANTED"
                          ? "Not required because no recovery action was recommended."
                          : agentStatus === "NO_ACTION" && step.key === "RECOVERY_EXECUTED"
                            ? "Not executed because no recovery action was required."
                            : agentStatus === "NO_ACTION" && step.key === "STATE_VERIFIED"
                              ? "Not required because recovery was not executed."
                              : agentStatus === "NO_ACTION" && step.key === "RESOLVED"
                                ? "SCÉANCE completed its assessment with no recovery action required."
                                : step.description
      return { ...step, state, description, time: audit?.timestamp }
    }),
  ]

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
      <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
        <ArrowLeft className="size-4" />
        Operations
      </Link>

      <header className="mt-8">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm text-muted-foreground">Recovery run</span>
          <span className="text-border">/</span>
          <span className="font-medium">{shipmentId}</span>
        </div>
        <div className="mt-5 flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">{shipment?.route.replace("->", "→") ?? "Operational disruption"}</h1>
              <span className="inline-flex items-center gap-2 rounded-full border border-border bg-muted/40 px-3 py-1 text-xs font-medium">
                <Circle className="size-2 fill-current" />
                {label(agentStatus)}
              </span>
            </div>
            <p className="mt-3 text-base text-muted-foreground">
              {agentStatus === "REJECTED"
                ? "The operator declined the proposed recovery action. No recovery workflow was executed."
                : agentStatus === "NO_ACTION"
                  ? "SCÉANCE determined that no recovery action is required."
                  : action
                    ? `Recommended action: ${label(action)}`
                    : "Recovery workflow in progress."}
            </p>
          </div>
          <div className="text-sm text-muted-foreground">
            Run ID
            <div className="mt-1 font-mono text-xs text-foreground">{runId}</div>
          </div>
        </div>
      </header>

      {/* Side-by-Side: Recovery Timeline (~60%) & SCÉANCE Activity (~40%) */}
      <div className="mt-10 grid grid-cols-1 gap-8 lg:grid-cols-12 lg:items-center">
        <section className="lg:col-span-7">
          <div className="h-full rounded-2xl border border-border bg-card">
            <div className="border-b border-border px-6 py-5">
              <h2 className="font-medium">Recovery timeline</h2>
              <p className="mt-1 text-sm text-muted-foreground">Observable operational actions and results.</p>
            </div>
            <div className="px-6 py-7">
              {timeline.map((event, index) => {
                const isLast = index === timeline.length - 1
                const isComplete = event.state === "completed"
                const isCurrent = event.state === "current"
                return (
                  <div key={event.key} className="relative flex gap-4">
                    {!isLast && (
                      <div className={`absolute left-[7px] top-5 h-full w-px ${isComplete ? "bg-foreground/20" : "bg-border"}`} />
                    )}
                    <div className="relative z-10 flex size-4 shrink-0 items-center justify-center">
                      {isComplete ? (
                        <span className="flex size-4 shrink-0 items-center justify-center rounded-full bg-foreground text-background">
                          <Check className="size-2.5" strokeWidth={3} />
                        </span>
                      ) : isCurrent ? (
                        <span className="relative flex size-4 shrink-0 items-center justify-center">
                          <span className="absolute size-3.5 rounded-full bg-emerald-500/25 animate-pulse" />
                          <span className="relative size-2 rounded-full bg-emerald-500" />
                        </span>
                      ) : event.state === "not-applicable" ? (
                        <span className="flex size-4 shrink-0 items-center justify-center">
                          <span className="size-2 rounded-full bg-muted-foreground/20" />
                        </span>
                      ) : (
                        <span className="flex size-4 shrink-0 items-center justify-center">
                          <span className="size-2.5 rounded-full border border-border bg-background" />
                        </span>
                      )}
                    </div>
                    <div className="pb-9">
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className={`text-sm ${isCurrent ? "font-semibold text-foreground" : isComplete ? "font-medium text-foreground" : "text-muted-foreground"}`}>
                          {event.title}
                        </h3>
                        {event.state === "not-applicable" && <span className="text-xs text-muted-foreground">Not required</span>}
                        {event.time && event.key !== "DISRUPTION_DETECTED" && <span className="text-xs text-muted-foreground">{new Date(event.time).toLocaleString()}</span>}
                      </div>
                      <p className={`mt-1 max-w-xl text-sm leading-6 ${isCurrent ? "text-foreground/90" : "text-muted-foreground"}`}>
                        {event.description}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        <aside className="self-center lg:col-span-5">
          <AgentPanel status={agentStatus} activity={activity} onOpenApproval={() => setDismissedApprovalRunId(undefined)} />
          {decisionMutation.isError && <p className="mt-3 text-sm text-destructive">{decisionMutation.error.message}</p>}
        </aside>
      </div>

      {(agentStatus === "RESOLVED" || agentStatus === "REJECTED" || agentStatus === "NO_ACTION") && (
        <RunOutcomeSummary
          title={
            agentStatus === "RESOLVED"
              ? "Recovery verified"
              : agentStatus === "REJECTED"
                ? "Recommendation rejected"
                : "No recovery required"
          }
          shipmentId={shipmentId}
          route={shipment?.route.replace("->", "→")}
          priority={shipment?.priority}
          action={action}
          rationale={run?.approval?.recommendation_rationale}
          decision={
            agentStatus === "RESOLVED"
              ? "approved"
              : agentStatus === "REJECTED"
                ? "rejected"
                : "no-action"
          }
          delayMinutes={delayMinutes}
          projectedPenalty={projectedPenalty}
          recoveryCost={recoveryCost ?? run?.approval?.recovery_cost_eur ?? undefined}
          estimatedRecoveryHours={estimatedRecoveryHours}
          netBenefit={netBenefit}
          verifiedEta={verifiedEta}
          executionTimestamp={executionAudit?.timestamp}
        />
      )}

      <RecoveryApprovalDialog
        open={approvalOpen}
        shipmentId={shipmentId}
        route={shipment?.route.replace("->", "→")}
        action={action}
        rationale={run?.approval?.recommendation_rationale}
        recoveryCost={run?.approval?.recovery_cost_eur ?? undefined}
        estimatedRecoveryHours={run?.approval?.estimated_recovery_hours ?? undefined}
        projectedPenalty={projectedPenalty}
        isPending={decisionMutation.isPending}
        onOpenChange={(open) => setDismissedApprovalRunId(open ? undefined : runId)}
        onDecision={(decision) => {
          setDismissedApprovalRunId(runId)
          decisionMutation.mutate(decision)
        }}
      />
    </div>
  )
}

export default RunDetails
