export type OperationalStatus =
  | "AT_ORIGIN"
  | "IN_TRANSIT"
  | "DELAYED"
  | "DISRUPTED"
  | "RESOLVED"

export type AgentStatus =
  | "MONITORING"
  | "INVESTIGATING"
  | "AWAITING_APPROVAL"
  | "EXECUTING"
  | "VERIFYING"
  | "RESOLVED"
  | "NO_ACTION"

export type RunSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"

export interface Run {
  runId: string
  shipmentId: string
  route: string
  operationalStatus: OperationalStatus
  agentStatus: AgentStatus
  severity: RunSeverity
  eta: string
  disruption?: {
    type: string
    durationMinutes?: number
  }
}