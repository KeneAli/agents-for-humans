import { useMemo, useState } from "react"
import { Radio, Zap } from "lucide-react"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import type { Shipment } from "@/lib/api"

export interface SimulationConfig {
  shipmentId: string
  disruptionType: string
  delayMinutes: number
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
}

const disruptions = [
  {
    value: "VEHICLE_BREAKDOWN",
    label: "Vehicle breakdown",
  },
  {
    value: "DRIVER_UNAVAILABLE",
    label: "Driver unavailable",
  },
  {
    value: "ROAD_CLOSURE",
    label: "Road closure",
  },
  {
    value: "SEVERE_DELAY",
    label: "Severe delay",
  },
  {
    value: "WEATHER_DISRUPTION",
    label: "Weather disruption",
  },
]

function getSeverity(
  delayMinutes: number,
): SimulationConfig["severity"] {
  if (delayMinutes >= 720) return "CRITICAL"
  if (delayMinutes >= 240) return "HIGH"
  if (delayMinutes >= 60) return "MEDIUM"
  return "LOW"
}

interface SimulationDialogProps {
  shipments: Shipment[]
  isLoadingShipments: boolean
  shipmentError?: string
  submissionError?: string
  onSimulate: (config: SimulationConfig) => Promise<void>
  isSubmitting: boolean
}

function SimulationDialog({
  shipments,
  isLoadingShipments,
  shipmentError,
  submissionError,
  onSimulate,
  isSubmitting,
}: SimulationDialogProps) {
  const [open, setOpen] = useState(false)
  const [shipmentId, setShipmentId] = useState("")
  const [disruptionType, setDisruptionType] = useState(
    "VEHICLE_BREAKDOWN",
  )
  const [delayMinutes, setDelayMinutes] = useState(480)

  const selectedShipment = shipments.find(
    (shipment) => shipment.shipment_id === shipmentId,
  )

  const severity = useMemo(
    () => getSeverity(delayMinutes),
    [delayMinutes],
  )

  const handleSimulate = async () => {
    if (!shipmentId) return

    await onSimulate({
      shipmentId,
      disruptionType,
      delayMinutes,
      severity,
    })

    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="outline" />}>
        <Radio className="size-4" />
        Simulate disruption
      </DialogTrigger>

      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Simulate a disruption</DialogTitle>

          <DialogDescription>
            Create a controlled operational event for SCÉANCE
            to investigate and recover from.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Shipment */}
          <div>
            <label
              htmlFor="shipment"
              className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground"
            >
              Shipment
            </label>

            <select
              id="shipment"
              value={shipmentId}
              onChange={(event) =>
                setShipmentId(event.target.value)
              }
              className="mt-2 flex h-10 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="" disabled>
                {isLoadingShipments ? "Loading shipments..." : "Select a shipment"}
              </option>
              {shipments.map((shipment) => (
                <option key={shipment.shipment_id} value={shipment.shipment_id}>
                  {shipment.shipment_id} - {shipment.origin} → {shipment.destination}
                </option>
              ))}
            </select>
          </div>

          {/* Disruption */}
          <div>
            <label
              htmlFor="disruption"
              className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground"
            >
              Disruption
            </label>

            <select
              id="disruption"
              value={disruptionType}
              onChange={(event) =>
                setDisruptionType(event.target.value)
              }
              className="mt-2 flex h-10 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
            >
              {disruptions.map((disruption) => (
                <option
                  key={disruption.value}
                  value={disruption.value}
                >
                  {disruption.label}
                </option>
              ))}
            </select>
          </div>

          {/* Delay */}
          <div>
            <label
              htmlFor="delay"
              className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground"
            >
              Estimated delay
            </label>

            <div className="mt-2 flex items-center gap-3">
              <input
                id="delay"
                type="number"
                min={0}
                step={1}
                value={delayMinutes}
                onChange={(event) =>
                  setDelayMinutes(
                    Math.max(0, Number(event.target.value)),
                  )
                }
                className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
              />

              <span className="text-sm text-muted-foreground">
                minutes
              </span>
            </div>

            <p className="mt-2 text-xs text-muted-foreground">
              {delayMinutes >= 60
                ? `${Math.floor(delayMinutes / 60)}h ${
                    delayMinutes % 60
                  }m`
                : `${delayMinutes} minutes`}
            </p>
          </div>

          {/* Result */}
          <div className="flex items-start gap-3 rounded-xl bg-muted/50 p-4">
            <Zap className="mt-0.5 size-4 shrink-0 text-muted-foreground" />

            <div>
              <p className="text-sm font-medium">
                {severity.charAt(0) +
                  severity.slice(1).toLowerCase()} severity
              </p>

              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                {selectedShipment?.shipment_id ?? "The selected shipment"} will be marked as
                disrupted and SCÉANCE will begin investigating
                the event.
              </p>
            </div>
          </div>

          {(shipmentError || submissionError) && (
            <p className="text-sm text-destructive">
              {shipmentError ?? submissionError}
            </p>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
          >
            Cancel
          </Button>

          <Button
            onClick={handleSimulate}
            disabled={!shipmentId || isLoadingShipments || Boolean(shipmentError) || isSubmitting}
          >
            <Radio className="size-4" />
            {isSubmitting ? "Starting..." : "Trigger disruption"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default SimulationDialog