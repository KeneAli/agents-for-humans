import { ArrowUpRight, Truck } from "lucide-react"

import { Button } from "@/components/ui/button"
import StatusBadge from "@/components/StatusBadge"
import type { Run } from "@/types/run"

import { Link } from "react-router"

interface RunCardProps {
  run: Run
}

function RunCard({ run }: RunCardProps) {
  const isDisrupted = run.operationalStatus === "DISRUPTED"

  return (
    <div
      className={`group flex flex-col gap-4 px-6 py-5 transition-colors sm:flex-row sm:items-center sm:justify-between ${
        isDisrupted ? "bg-muted/30" : "hover:bg-muted/40"
      }`}
    >
      <div className="flex items-center gap-4">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl border border-border bg-background">
          <Truck className="size-4 text-muted-foreground" />
        </div>

        <div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="font-medium">{run.shipmentId}</span>

            <StatusBadge status={run.operationalStatus} />

            {isDisrupted && (
              <StatusBadge status={run.severity} />
            )}
          </div>

          <p className="mt-1 text-sm text-muted-foreground">
            {run.route}
          </p>

          {run.disruption && (
            <p className="mt-1 text-xs text-muted-foreground">
              {run.disruption.type.replaceAll("_", " ").toLowerCase()}
              {run.disruption.durationMinutes
                ? ` · ${run.disruption.durationMinutes} min`
                : ""}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-8 pl-14 text-sm sm:pl-0">
        <div>
          <p className="text-xs text-muted-foreground">Agent</p>
          <p className="mt-1">
            {run.agentStatus.replaceAll("_", " ").toLowerCase()}
          </p>
        </div>

        <div className="min-w-28">
          <p className="text-xs text-muted-foreground">
            Estimated arrival
          </p>
          <p className="mt-1">{run.eta}</p>
        </div>

        {isDisrupted && (
          <Link to={`/runs/${run.shipmentId}/${run.runId}`}>
            <Button variant="ghost" size="icon" aria-label="Open run">
              <ArrowUpRight className="size-4" />
            </Button>
          </Link>
        )}
      </div>
    </div>
  )
}

export default RunCard