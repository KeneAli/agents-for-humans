import {
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  FileCheck2,
  ShieldCheck,
  TrendingDown,
  UserCheck,
  XCircle,
} from "lucide-react"

export interface RunOutcomeSummaryProps {
  title: string
  shipmentId: string
  route?: string
  priority?: string
  action?: string | null
  rationale?: string | null
  decision: "approved" | "rejected" | "no-action"
  delayMinutes?: number
  projectedPenalty?: number
  recoveryCost?: number
  estimatedRecoveryHours?: number
  netBenefit?: number
  verifiedEta?: string
  executionTimestamp?: string
  verificationTimestamp?: string
}

function label(value: string) {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/^./, (character) => character.toUpperCase())
}

function formatCurrency(amount?: number) {
  if (amount === undefined || amount === null) return undefined
  return new Intl.NumberFormat("en-IE", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
  }).format(amount)
}

function RunOutcomeSummary({
  title,
  shipmentId,
  route,
  priority,
  action,
  rationale,
  decision,
  delayMinutes,
  projectedPenalty,
  recoveryCost,
  estimatedRecoveryHours,
  netBenefit,
  verifiedEta,
  executionTimestamp,
}: RunOutcomeSummaryProps) {
  const isResolved = decision === "approved"
  const isRejected = decision === "rejected"
  const isNoAction = decision === "no-action"

  return (
    <section className="mt-10 rounded-2xl border border-border bg-card p-6 sm:p-8">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            {isResolved && <CheckCircle2 className="size-5 text-emerald-500" />}
            {isRejected && <XCircle className="size-5 text-amber-500" />}
            {isNoAction && <CheckCircle2 className="size-5 text-blue-500" />}
            <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
          </div>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Operational recovery debrief and verified outcome for{" "}
            <span className="font-medium text-foreground">{shipmentId}</span>
            {route ? ` (${route})` : ""}
            {priority ? ` · ${priority} priority` : ""}
          </p>
        </div>

        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
            isResolved
              ? "border border-emerald-500/20 bg-emerald-500/10 text-emerald-500"
              : isRejected
                ? "border border-amber-500/20 bg-amber-500/10 text-amber-500"
                : "border border-blue-500/20 bg-blue-500/10 text-blue-500"
          }`}
        >
          {isResolved
            ? "Workflow Completed & Verified"
            : isRejected
              ? "Recommendation Rejected"
              : "No Action Needed"}
        </span>
      </div>

      {/* Grid of operational facts */}
      <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {/* Disruption & Impact */}
        <div className="rounded-xl border border-border bg-muted/30 p-4">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            <AlertTriangle className="size-3.5" />
            Disruption & Delay
          </div>
          <div className="mt-3 space-y-1">
            <p className="text-sm font-semibold">
              {delayMinutes !== undefined
                ? `${delayMinutes} min (${(delayMinutes / 60).toFixed(1)}h) delay`
                : "Operational disruption"}
            </p>
            {projectedPenalty !== undefined && (
              <p className="text-xs text-muted-foreground">
                Projected SLA penalty:{" "}
                <span className="font-medium text-foreground">
                  {formatCurrency(projectedPenalty)}
                </span>
              </p>
            )}
          </div>
        </div>

        {/* Investigated Strategy */}
        <div className="rounded-xl border border-border bg-muted/30 p-4">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            <FileCheck2 className="size-3.5" />
            Selected Recovery Action
          </div>
          <div className="mt-3 space-y-1">
            <p className="text-sm font-semibold">
              {action ? label(action) : "Do Nothing"}
            </p>
            {rationale && (
              <p className="text-xs leading-5 text-muted-foreground">
                {rationale}
              </p>
            )}
          </div>
        </div>

        {/* Human Authorization */}
        <div className="rounded-xl border border-border bg-muted/30 p-4">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            <UserCheck className="size-3.5" />
            Human Authorization
          </div>
          <div className="mt-3 space-y-1">
            <p className="text-sm font-semibold">
              {isResolved
                ? "Authorized by Operator"
                : isRejected
                  ? "Declined by Operator"
                  : "Not Required (Within Tolerance)"}
            </p>
            <p className="text-xs text-muted-foreground">
              {isResolved
                ? "Approved via human-in-the-loop intervention."
                : isRejected
                  ? "Execution aborted per human override."
                  : "Absorbed without SLA breach."}
            </p>
          </div>
        </div>

        {/* Recovery Economics */}
        {action && action !== "DO_NOTHING" && (
          <div className="rounded-xl border border-border bg-muted/30 p-4">
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              <DollarSign className="size-3.5" />
              Recovery Economics
            </div>
            <div className="mt-3 space-y-1.5 text-xs">
              {recoveryCost !== undefined && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Recovery cost:</span>
                  <span className="font-medium">{formatCurrency(recoveryCost)}</span>
                </div>
              )}
              {estimatedRecoveryHours !== undefined && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Time recovered:</span>
                  <span className="font-medium">{estimatedRecoveryHours.toFixed(1)}h</span>
                </div>
              )}
              {netBenefit !== undefined && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Net benefit:</span>
                  <span className="font-medium text-emerald-500">
                    {formatCurrency(netBenefit)}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Execution Result */}
        <div className="rounded-xl border border-border bg-muted/30 p-4">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            <TrendingDown className="size-3.5" />
            Execution Result
          </div>
          <div className="mt-3 space-y-1">
            <p className="text-sm font-semibold">
              {isResolved
                ? "Executed Successfully"
                : isRejected
                  ? "Execution Bypassed"
                  : "No Execution Required"}
            </p>
            {executionTimestamp && isResolved && (
              <p className="text-xs text-muted-foreground">
                Applied at {new Date(executionTimestamp).toLocaleTimeString()}
              </p>
            )}
          </div>
        </div>

        {/* Verification Result */}
        <div className="rounded-xl border border-border bg-muted/30 p-4">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            <ShieldCheck className="size-3.5" />
            Verification Result
          </div>
          <div className="mt-3 space-y-1">
            <p className="text-sm font-semibold">
              {isResolved
                ? "Operational State Verified"
                : isRejected
                  ? "Unmitigated (Original ETA)"
                  : "Verified Within SLA"}
            </p>
            {verifiedEta && isResolved && (
              <p className="text-xs text-muted-foreground">
                Revised ETA:{" "}
                <span className="font-medium text-foreground">
                  {new Date(verifiedEta).toLocaleString()}
                </span>
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Synthesis / Operational Summary */}
      <div className="mt-6 rounded-xl border border-border/80 bg-muted/15 p-5">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">
          Operational Summary
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          {isResolved && (
            <>
              SCÉANCE identified the {delayMinutes ? `${delayMinutes}-minute` : ""} disruption on{" "}
              <strong className="text-foreground">{shipmentId}</strong>, evaluated deterministic recovery options, and recommended{" "}
              <strong className="text-foreground">{label(action ?? "EXPEDITED_TRANSPORT")}</strong>
              {rationale ? ` (${rationale.toLowerCase()})` : ""}. Upon human authorization, the recovery was executed
              {recoveryCost ? ` at a cost of ${formatCurrency(recoveryCost)}` : ""}
              {estimatedRecoveryHours ? `, recovering approximately ${estimatedRecoveryHours.toFixed(1)} hours` : ""}. The live operational state was verified with status <code className="rounded bg-muted px-1.5 py-0.5 text-xs text-foreground">RECOVERY_IN_PROGRESS</code>
              {verifiedEta ? ` and an updated ETA of ${new Date(verifiedEta).toLocaleString()}` : ""}, successfully mitigating customer SLA breach risk.
            </>
          )}
          {isRejected && (
            <>
              SCÉANCE investigated the disruption on <strong className="text-foreground">{shipmentId}</strong> and prepared a recovery recommendation of{" "}
              <strong className="text-foreground">{label(action ?? "recovery")}</strong>. The operator declined the proposed recommendation. In accordance with policy, automated execution was bypassed, leaving the shipment on its unmitigated trajectory with a projected SLA penalty of{" "}
              <strong className="text-foreground">{formatCurrency(projectedPenalty) ?? "standard liability"}</strong>.
            </>
          )}
          {isNoAction && (
            <>
              SCÉANCE evaluated the disruption on <strong className="text-foreground">{shipmentId}</strong> against contract SLA tolerances and determined that the delay does not breach delivery commitments. No costly carrier interventions were required, preserving operational budget with zero penalties.
            </>
          )}
        </p>
      </div>
    </section>
  )
}

export default RunOutcomeSummary
