import { Circle, Radio } from "lucide-react"

import SimulationDialog from "@/components/SimulationDialog"
import RunCard from "@/components/RunCard"
import { useSimulation } from "@/context/SimulationContext"

const shipmentIds = [
  "SHP-0048",
  "SHP-0127",
  "SHP-0214",
  "SHP-0319",
]

function Operations() {
  const { simulateDisruption, getRuns } = useSimulation()

  const displayedRuns = shipmentIds.flatMap((shipmentId) =>
    getRuns(shipmentId),
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
            onSimulate={simulateDisruption}
          />
        </div>

        <div className="divide-y divide-border">
          {displayedRuns.map((run) => (
            <RunCard key={run.runId} run={run} />
          ))}
        </div>
      </section>
    </div>
  )
}

export default Operations