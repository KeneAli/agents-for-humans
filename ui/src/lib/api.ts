import { z } from "zod"

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ??
  "https://r22h32x4wcr3mpqidb64v7z3ei0dqzyw.lambda-url.us-east-1.on.aws"
).replace(/\/$/, "")

const shipmentSchema = z.object({
  shipment_id: z.string(),
  origin: z.string(),
  destination: z.string(),
  route: z.string(),
  eta: z.string(),
  status: z.string(),
  priority: z.string(),
})

const approvalSchema = z.object({
  event_id: z.string().optional(),
  shipment_id: z.string(),
  run_id: z.string(),
  runtime_session_id: z.string().optional(),
  interrupt_id: z.string().optional(),
  requested_tool: z.string().optional(),
  option_type: z.string().nullable().optional(),
  status: z.string().optional(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),
  expires_at: z.string().optional(),
  selected_action: z.string().optional(),
  recommendation_rationale: z.string().nullable().optional(),
  recovery_cost_eur: z.number().nullable().optional(),
  estimated_recovery_hours: z.number().nullable().optional(),
  projected_sla_penalty_eur: z.number().nullable().optional(),
}).passthrough()

const workflowSchema = z.object({
  event_id: z.string().nullable().optional(),
  shipment_id: z.string(),
  run_id: z.string(),
  runtime_session_id: z.string().nullable().optional(),
  status: z.string(),
  action: z.string().nullable().optional(),
}).passthrough()

const auditEventSchema = z.object({
  event_type: z.string(),
  timestamp: z.string(),
  details: z.record(z.string(), z.unknown()),
})

const runSchema = z.object({
  shipment_id: z.string(),
  run_id: z.string(),
  approval: approvalSchema.nullable(),
  workflow: workflowSchema.nullable(),
  audit_events: z.array(auditEventSchema),
})

const createDisruptionSchema = z.object({
  event_id: z.string(),
  shipment_id: z.string(),
  run_id: z.string(),
  status: z.literal("published"),
})

const decisionSchema = z.object({
  shipment_id: z.string(),
  run_id: z.string(),
  event_id: z.string().optional(),
  status: z.string(),
}).passthrough()

export type Shipment = z.infer<typeof shipmentSchema>
export type RecoveryRun = z.infer<typeof runSchema>
export type CreateDisruptionResponse = z.infer<typeof createDisruptionSchema>
export type DecisionResponse = z.infer<typeof decisionSchema>

export interface CreateDisruptionInput {
  event_id: string
  event_type: string
  shipment_id: string
  delay_minutes: number
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  source: string
  timestamp: string
  description: string
}

export class ApiError extends Error {
  readonly status: number

  constructor(
    message: string,
    status: number,
  ) {
    super(message)
    this.status = status
  }
}

async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init)
  } catch {
    throw new Error("Unable to reach the operations control plane.")
  }

  let body: unknown
  try {
    body = await response.json()
  } catch {
    throw new Error("The operations control plane returned invalid JSON.")
  }

  if (!response.ok) {
    const message =
      typeof body === "object" && body !== null && "error" in body
        ? String(body.error)
        : `Request failed with status ${response.status}.`
    throw new ApiError(message, response.status)
  }

  const parsed = schema.safeParse(body)
  if (!parsed.success) {
    throw new Error("The operations control plane returned an unexpected response.")
  }

  return parsed.data
}

export function getShipments() {
  return request("/shipments", z.object({ shipments: z.array(shipmentSchema) }))
}

export function createDisruption(input: CreateDisruptionInput) {
  return request("/disruptions", createDisruptionSchema, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  })
}

export function getRun(shipmentId: string, runId: string) {
  return request(
    `/runs/${encodeURIComponent(shipmentId)}/${encodeURIComponent(runId)}`,
    runSchema,
  )
}

export function submitDecision(
  shipmentId: string,
  runId: string,
  decision: "approve" | "reject",
) {
  return request(
    `/runs/${encodeURIComponent(shipmentId)}/${encodeURIComponent(runId)}/decision`,
    decisionSchema,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision }),
    },
  )
}
