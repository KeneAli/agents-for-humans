import { useMemo, useState } from "react"
import { Search } from "lucide-react"
import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "react-router"

import SimulationDialog from "@/components/SimulationDialog"
import RunCard from "@/components/RunCard"
import { createDisruption } from "@/lib/api"
import { useShipments } from "@/hooks/useShipments"
import type { Run } from "@/types/run"

const DEMO_PRIORITY_IDS = new Set([
  "SHP-0008",
  "SHP-0048",
  "SHP-0047",
  "SHP-0046",
  "SHP-0001",
  "SHP-0002",
  "SHP-0003",
  "SHP-0004",
  "SHP-0005",
  "SHP-0006",
  "SHP-0007",
  "SHP-0010",
])

function Operations() {
  const navigate = useNavigate()
  const shipmentsQuery = useShipments()
  const [searchQuery, setSearchQuery] = useState("")
  const [showAll, setShowAll] = useState(false)

  const createDisruptionMutation = useMutation({
    mutationFn: createDisruption,
    onSuccess: (response) => {
      navigate(`/runs/${response.shipment_id}/${response.run_id}`)
    },
  })

  const allRuns: Run[] = useMemo(() => {
    return (shipmentsQuery.data?.shipments ?? []).map((shipment) => ({
      runId: shipment.shipment_id,
      shipmentId: shipment.shipment_id,
      route: shipment.route.replace("->", "→"),
      operationalStatus:
        shipment.status === "DELAYED"
          ? ("DISRUPTED" as const)
          : shipment.status === "IN_TRANSIT"
            ? ("IN_TRANSIT" as const)
            : ("AT_ORIGIN" as const),
      agentStatus:
        shipment.status === "DELAYED"
          ? ("INVESTIGATING" as const)
          : ("MONITORING" as const),
      severity: shipment.status === "DELAYED" ? ("HIGH" as const) : ("LOW" as const),
      eta: new Date(shipment.eta).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }),
    }))
  }, [shipmentsQuery.data?.shipments])

  // Sort: disrupted/delayed first, then demo priority IDs, then standard order
  const sortedRuns = useMemo(() => {
    return [...allRuns].sort((a, b) => {
      const aDisrupted = a.operationalStatus === "DISRUPTED"
      const bDisrupted = b.operationalStatus === "DISRUPTED"
      if (aDisrupted && !bDisrupted) return -1
      if (!aDisrupted && bDisrupted) return 1

      const aPriority = DEMO_PRIORITY_IDS.has(a.shipmentId)
      const bPriority = DEMO_PRIORITY_IDS.has(b.shipmentId)
      if (aPriority && !bPriority) return -1
      if (!aPriority && bPriority) return 1

      return a.shipmentId.localeCompare(b.shipmentId)
    })
  }, [allRuns])

  const filteredRuns = useMemo(() => {
    const query = searchQuery.trim().toLowerCase()
    if (!query) return sortedRuns
    return sortedRuns.filter(
      (run) =>
        run.shipmentId.toLowerCase().includes(query) ||
        run.route.toLowerCase().includes(query) ||
        run.operationalStatus.toLowerCase().includes(query),
    )
  }, [sortedRuns, searchQuery])

  const displayedRuns = useMemo(() => {
    if (searchQuery.trim() || showAll) {
      return filteredRuns
    }
    return filteredRuns.slice(0, 10)
  }, [filteredRuns, searchQuery, showAll])

  const disruptedRuns = allRuns.filter(
    (run) => run.operationalStatus === "DISRUPTED",
  )

  const totalShipments = shipmentsQuery.data?.shipments.length ?? allRuns.length

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
      {/* Network Monitoring Hero Banner */}
      <section className="relative overflow-hidden rounded-2xl border border-border bg-card p-6 sm:p-8">
        <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                Network Monitoring
              </span>
            </div>
            <p className="mt-1.5 text-sm text-muted-foreground">
              Continuous operational surveillance across European logistics corridors.
            </p>

            <div className="mt-5 flex items-baseline gap-2.5">
              <span className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                {totalShipments}
              </span>
              <span className="text-sm text-muted-foreground">
                active shipments
              </span>
            </div>
          </div>

          <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center md:flex-col md:items-end">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-muted/40 px-3.5 py-1.5 text-xs font-medium text-foreground">
              <span className="relative flex size-2">
                <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-60 duration-1000" />
                <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
              </span>
              <span>Agent online</span>
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

      {/* Shipment Catalogue */}
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

          {/* Quick search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search shipments..."
              className="h-9 w-44 rounded-lg border border-border bg-background pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:border-foreground focus:outline-none sm:w-56"
            />
          </div>
        </div>

        <div className="divide-y divide-border">
          {shipmentsQuery.isLoading && (
            <p className="px-6 py-8 text-sm text-muted-foreground">Loading shipments...</p>
          )}

          {shipmentsQuery.isError && (
            <p className="px-6 py-8 text-sm text-muted-foreground">Unable to load shipments.</p>
          )}

          {displayedRuns.length === 0 && !shipmentsQuery.isLoading && (
            <p className="px-6 py-8 text-sm text-muted-foreground">No shipments matching your query.</p>
          )}

          {displayedRuns.map((run) => (
            <RunCard key={run.runId} run={run} />
          ))}
        </div>

        {/* Footer info & toggle for larger catalogue */}
        {!searchQuery.trim() && totalShipments > 10 && (
          <div className="flex items-center justify-between border-t border-border px-6 py-4 text-xs text-muted-foreground">
            <span>
              Showing {showAll ? totalShipments : Math.min(10, totalShipments)} of {totalShipments} shipments
            </span>
            <button
              type="button"
              onClick={() => setShowAll((prev) => !prev)}
              className="font-medium text-foreground transition-colors hover:underline"
            >
              {showAll ? "Show fewer" : `View all (${totalShipments})`}
            </button>
          </div>
        )}
      </section>
    </div>
  )
}

export default Operations