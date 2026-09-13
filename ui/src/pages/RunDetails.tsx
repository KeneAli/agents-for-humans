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

const recoverySteps = [
  { key: "OPTIONS_EVALUATED", title: "Agent investigated", description: "Shipment context and recovery options were evaluated." },
  { key: "RECOVERY_SELECTED", title: "Recovery recommended", description: "The best available recovery option was selected." },
  { key: "APPROVAL_GRANTED", title: "Human decision", description: "The recommended recovery is awaiting an operator decision." },
  { key: "RECOVERY_EXECUTED", title: "Recovery execution", description: "The authorized recovery action will execute after approval." },
  { key: "STATE_VERIFIED", title: "Verification", description: "The resulting shipment state will be verified after execution." },
  { key: "RESOLVED", title: "Resolved", description: "The recovery workflow completes after verification." },
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

function stateForStep(
  stepKey: string,
  hasAudit: boolean,
  auditKeys: Set<string>,
  agentStatus: AgentStatus,
): TimelineState {
  if (hasAudit || (stepKey === "RESOLVED" && agentStatus === "RESOLVED")) return "completed"
  if (agentStatus === "REJECTED") {
    if (stepKey === "APPROVAL_GRANTED") return "completed"
    if (["RECOVERY_EXECUTED", "STATE_VERIFIED"].includes(stepKey)) return "not-applicable"
    if (stepKey === "RESOLVED") return "completed"
  }
  if (agentStatus === "NO_ACTION") {
    if (["APPROVAL_GRANTED", "RECOVERY_EXECUTED", "STATE_VERIFIED"].includes(stepKey)) return "not-applicable"
    if (stepKey === "RESOLVED") return "completed"
  }
  if (stepKey === "OPTIONS_EVALUATED" && !auditKeys.has("OPTIONS_EVALUATED")) return "current"
  const firstMissing = recoverySteps.find((step) => !auditKeys.has(step.key))
  return firstMissing?.key === stepKey ? "current" : "pending"
}

function activityForRun(
  agentStatus: AgentStatus,
  auditEvents: Array<{ event_type: string; timestamp: string }>,
): ActivityItem[] {
  const byType = new Map(auditEvents.map((event) => [event.event_type, event]))
  const definitions = [
    {
      started: "SHIPMENT_CONTEXT_REVIEW_STARTED",
      completed: "SHIPMENT_CONTEXT_REVIEWED",
      label: "Shipment context reviewed",
      activeLabel: "Reviewing shipment context",
      description: "Checking current shipment status and delivery window.",
    },
    {
      started: "DELAY_IMPACT_ASSESSMENT_STARTED",
      completed: "DELAY_IMPACT_ASSESSED",
      label: "Delay impact assessed",
      activeLabel: "Assessing delay impact",
      description: "Calculating expected impact on delivery.",
    },
    {
      started: "RECOVERY_OPTIONS_EVALUATION_STARTED",
      completed: "OPTIONS_EVALUATED",
      label: "Recovery options evaluated",
      activeLabel: "Evaluating recovery options",
      description: "Comparing available recovery strategies.",
    },
    {
      completed: "RECOMMENDATION_PREPARED",
      label: "Recovery recommendation prepared",
      activeLabel: "Preparing recommendation",
      description: "Preparing the selected action for operator review.",
    },
    {
      completed: "APPROVAL_REQUESTED",
      label: "Awaiting operator approval",
      activeLabel: "Awaiting operator approval",
      description: "Waiting for an operator decision before recovery can proceed.",
    },
    {
      started: "RECOVERY_EXECUTION_STARTED",
      completed: "RECOVERY_EXECUTED",
      label: "Recovery workflow completed",
      activeLabel: "Executing selected recovery",
      description: "Applying the authorized recovery action.",
    },
    {
      started: "VERIFICATION_STARTED",
      completed: "VERIFICATION_COMPLETED",
      label: "Shipment state verified",
      activeLabel: "Verifying recovery",
      description: "Checking the resulting shipment state.",
    },
  ]

  const items: ActivityItem[] = []
  for (const definition of definitions) {
    const completed = byType.get(definition.completed)
    if (completed) {
      items.push({ label: definition.label, description: definition.description, state: "completed", timestamp: completed.timestamp })
      continue
    }
    const started = definition.started ? byType.get(definition.started) : undefined
    if (started) {
      items.push({ label: definition.activeLabel, description: definition.description, state: "current", timestamp: started.timestamp })
    }
  }

  if (agentStatus === "REJECTED") {
    items.push({ label: "Operator declined recommendation", state: "completed" })
  }
  if (agentStatus === "NO_ACTION") {
    items.push({ label: "No recovery required", state: "completed" })
  }
  if (items.length === 0 && agentStatus === "INVESTIGATING") {
    return [{ label: "Investigation started", description: "Waiting for the first operational activity event.", state: "current" }]
  }
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
          label: "Reviewing shipment context",
          description: "Checking current shipment status and delivery window.",
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
    ...recoverySteps.map((step) => {
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
    <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8">
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
              <h1 className="text-4xl font-semibold tracking-tight">{shipment?.route.replace("->", "→") ?? "Operational disruption"}</h1>
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

      <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_360px]">
        <section>
          <div className="rounded-2xl border border-border bg-card">
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
                    {!isLast && <div className={`absolute left-[7px] top-5 h-full w-px ${isComplete ? "bg-foreground/20" : "bg-border"}`} />}
                    <div className="relative z-10 flex size-4 shrink-0 items-center justify-center">
                      {isComplete ? <div className="flex size-4 items-center justify-center rounded-full bg-foreground text-background"><Check className="size-2.5" strokeWidth={3} /></div> : isCurrent ? <div className="flex size-4 items-center justify-center rounded-full border-2 border-foreground bg-background"><div className="size-1.5 rounded-full bg-foreground" /></div> : <div className="size-3 rounded-full border border-border bg-background" />}
                    </div>
                    <div className="pb-9">
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className={`text-sm font-medium ${event.state === "pending" || event.state === "not-applicable" ? "text-muted-foreground" : ""}`}>{event.title}</h3>
                        {event.state === "not-applicable" && <span className="text-xs text-muted-foreground">Not required</span>}
                        {event.time && event.key !== "DISRUPTION_DETECTED" && <span className="text-xs text-muted-foreground">{new Date(event.time).toLocaleString()}</span>}
                      </div>
                      <p className="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">{event.description}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        <aside>
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
