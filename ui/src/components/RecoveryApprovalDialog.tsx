import { ShieldCheck } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface RecoveryApprovalDialogProps {
  open: boolean
  shipmentId: string
  route?: string
  action?: string | null
  rationale?: string | null
  recoveryCost?: number
  estimatedRecoveryHours?: number
  projectedPenalty?: number
  isPending: boolean
  onOpenChange: (open: boolean) => void
  onDecision: (decision: "approve" | "reject") => void
}

function label(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/^./, (character) => character.toUpperCase())
}

function RecoveryApprovalDialog({
  open,
  shipmentId,
  route,
  action,
  rationale,
  recoveryCost,
  estimatedRecoveryHours,
  projectedPenalty,
  isPending,
  onOpenChange,
  onDecision,
}: RecoveryApprovalDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" showCloseButton={!isPending}>
        <DialogHeader>
          <DialogTitle>Recovery recommendation</DialogTitle>
          <DialogDescription>
            SCÉANCE completed its investigation and needs your authorization before recovery can proceed.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-3">
          <div className="border-y border-border py-4">
            <p className="text-sm font-medium">{shipmentId}</p>
            {route && <p className="mt-1 text-sm text-muted-foreground">{route}</p>}
          </div>

          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 size-4 shrink-0" />
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">SCÉANCE recommends</p>
              <p className="mt-2 text-lg font-medium">{action ? label(action) : "Recovery action"}</p>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {rationale ?? "The recommendation was selected from the evaluated recovery options and requires an operator decision before execution."}
              </p>
            </div>
          </div>

          {(recoveryCost !== undefined || projectedPenalty !== undefined || estimatedRecoveryHours !== undefined) && (
            <div className="space-y-3 border-l-2 border-foreground/20 pl-4 text-sm">
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Decision context</p>
              {recoveryCost !== undefined && <p>Recovery cost <span className="float-right font-medium">€{recoveryCost.toFixed(2)}</span></p>}
              {projectedPenalty !== undefined && <p>SLA exposure without recovery <span className="float-right font-medium">€{projectedPenalty.toFixed(2)}</span></p>}
              {estimatedRecoveryHours !== undefined && <p>Estimated recovery time <span className="float-right font-medium">{estimatedRecoveryHours}h</span></p>}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onDecision("reject")} disabled={isPending}>Reject</Button>
          <Button onClick={() => onDecision("approve")} disabled={isPending}>
            {isPending ? "Submitting..." : "Approve recovery"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default RecoveryApprovalDialog
