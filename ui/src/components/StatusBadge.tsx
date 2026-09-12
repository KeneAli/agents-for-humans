import { Circle } from "lucide-react"

import type {
  OperationalStatus,
  RunSeverity,
} from "@/types/run"

interface StatusBadgeProps {
  status: OperationalStatus | RunSeverity
}

const labels: Record<StatusBadgeProps["status"], string> = {
  AT_ORIGIN: "At origin",
  IN_TRANSIT: "In transit",
  DELAYED: "Delayed",
  DISRUPTED: "Disrupted",
  RESOLVED: "Resolved",
  LOW: "Low",
  MEDIUM: "Medium",
  HIGH: "High",
  CRITICAL: "Critical",
}

function StatusBadge({ status }: StatusBadgeProps) {
  const isSeverity = ["LOW", "MEDIUM", "HIGH", "CRITICAL"].includes(status)

  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
      <Circle className="size-1.5 fill-current" />
      {labels[status]}
      {isSeverity && " severity"}
    </span>
  )
}

export default StatusBadge