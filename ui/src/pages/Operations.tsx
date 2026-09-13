import { Circle, Radio } from "lucide-react"
import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "react-router"

import SimulationDialog from "@/components/SimulationDialog"
import RunCard from "@/components/RunCard"
import { createDisruption } from "@/lib/api"
import { useShipments } from "@/hooks/useShipments"
import type { Run } from "@/types/run"

function Operations() {
  const navigate = useNavigate()
  const shipmentsQuery = useShipments()
  const createDisruptionMutation = useMutation({
    mutationFn: createDisruption,
    onSuccess: (response) => {
      navigate(`/runs/${response.shipment_id}/${response.run_id}`)
    },
  })

  const displayedRuns: Run[] = (shipmentsQuery.data?.shipments ?? []).map(
    (shipment) => ({
      runId: shipment.shipment_id,
      shipmentId: shipment.shipment_id,
      route: shipment.route.replace("->", "→"),
      operationalStatus: shipment.status === "IN_TRANSIT" ? "IN_TRANSIT" : "AT_ORIGIN",
      agentStatus: "MONITORING",
      severity: "LOW",
      eta: new Date(shipment.eta).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }),
    }),
  )

  const disruptedRuns = displayedRuns.filter(
    (run) => run.operationalStatus === "DISRUPTED",
  )

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
      <section>
        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
          <Radio className="size-3.5" />
          Operations control
        </div>

        <div className="mt-5 flex flex-col justify-between gap-8 md:flex-row md:items-end">
          <div>
            <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">
              Good evening.
            </h1>

            <p className="mt-3 max-w-xl text-base leading-7 text-muted-foreground">
              SCÉANCE is monitoring your logistics network for
              disruptions that need attention.
            </p>
          </div>

          <div className="flex items-center gap-3 text-sm">
            <span className="flex items-center gap-2 text-muted-foreground">
              <Circle className="size-2 fill-current text-emerald-500" />
              Agent online
            </span>

            <span className="text-border">|</span>

            <span>
              <strong>{displayedRuns.length}</strong>{" "}
              <span className="text-muted-foreground">
                active runs
              </span>
            </span>
          </div>
        </div>
      </section>

      {disruptedRuns.length > 0 && (
        <section className="mt-10">
          <div className="mb-4">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
              Needs attention
            </p>

            <h2 className="mt-2 text-xl font-semibold tracking-tight">
              {disruptedRuns.length}{" "}
              {disruptedRuns.length === 1
                ? "disruption"
                : "disruptions"}{" "}
              requiring action
            </h2>
          </div>

          <div className="overflow-hidden rounded-2xl border border-border bg-card">
            {disruptedRuns.map((run) => (
              <RunCard key={run.runId} run={run} />
            ))}
          </div>
        </section>
      )}

      <section className="mt-10 rounded-2xl border border-border bg-card">
        <div className="flex flex-col gap-4 border-b border-border px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-medium">
              Network activity
            </h2>

            <p className="mt-1 text-sm text-muted-foreground">
              Live operational state across monitored shipments.
            </p>
          </div>

          <SimulationDialog
            shipments={shipmentsQuery.data?.shipments ?? []}
            isLoadingShipments={shipmentsQuery.isLoading}
            shipmentError={shipmentsQuery.error?.message}
            submissionError={createDisruptionMutation.error?.message}
            isSubmitting={createDisruptionMutation.isPending}
            onSimulate={async (config) => {
              await createDisruptionMutation.mutateAsync({
                event_id: `SIM-UI-${crypto.randomUUID().replaceAll("-", "")}`,
                event_type: config.disruptionType,
                shipment_id: config.shipmentId,
                delay_minutes: config.delayMinutes,
                severity: config.severity,
                source: "sceance-ui",
                timestamp: new Date().toISOString(),
                description: `${config.disruptionType.replaceAll("_", " ")} causing an estimated ${config.delayMinutes}-minute disruption.`,
              })
            }}
          />
        </div>

        <div className="divide-y divide-border">
          {shipmentsQuery.isLoading && (
            <p className="px-6 py-8 text-sm text-muted-foreground">Loading shipments...</p>
          )}

          {shipmentsQuery.isError && (
            <p className="px-6 py-8 text-sm text-muted-foreground">Unable to load shipments.</p>
          )}

          {displayedRuns.map((run) => (
            <RunCard key={run.runId} run={run} />
          ))}
        </div>
      </section>
    </div>
  )
}

export default Operations