import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import type { AgentStatus, Run } from "@/types/run"
import type { SimulationConfig } from "@/components/SimulationDialog"

interface SimulationContextValue {
  simulatedRuns: Record<string, Run>
  simulateDisruption: (config: SimulationConfig) => void
  updateAgentStatus: (
    shipmentId: string,
    runId: string,
    status: AgentStatus,
  ) => void
  getRuns: (shipmentId: string) => Run[]
  getRun: (shipmentId: string, runId: string) => Run | undefined
}

const SimulationContext =
  createContext<SimulationContextValue | null>(null)

const baseRuns: Run[] = [
  {
    runId: "RUN-ef115df1404545d4b4cd0996dd30a339",
    shipmentId: "SHP-0048",
    route: "Lagos → Accra",
    operationalStatus: "IN_TRANSIT",
    agentStatus: "MONITORING",
    severity: "LOW",
    eta: "Today, 18:40",
  },
  {
    runId: "RUN-0127",
    shipmentId: "SHP-0127",
    route: "Abidjan → Lagos",
    operationalStatus: "IN_TRANSIT",
    agentStatus: "MONITORING",
    severity: "LOW",
    eta: "Tomorrow, 09:15",
  },
  {
    runId: "RUN-0214",
    shipmentId: "SHP-0214",
    route: "Accra → Kumasi",
    operationalStatus: "AT_ORIGIN",
    agentStatus: "MONITORING",
    severity: "LOW",
    eta: "Tomorrow, 14:30",
  },
  {
    runId: "RUN-0319",
    shipmentId: "SHP-0319",
    route: "Lagos → Ibadan",
    operationalStatus: "IN_TRANSIT",
    agentStatus: "MONITORING",
    severity: "LOW",
    eta: "Today, 21:10",
  },
]

function createRunId() {
  return `RUN-${crypto.randomUUID().replaceAll("-", "")}`
}

export function SimulationProvider({
  children,
}: {
  children: ReactNode
}) {
  const [simulatedRuns, setSimulatedRuns] =
    useState<Record<string, Run>>({})

  const simulateDisruption = (config: SimulationConfig) => {
    const baseRun = baseRuns.find(
      (run) => run.shipmentId === config.shipmentId,
    )

    if (!baseRun) return

    const runId = createRunId()

    const simulatedRun: Run = {
      ...baseRun,
      runId,
      operationalStatus: "DISRUPTED",
      agentStatus: "INVESTIGATING",
      severity: config.severity,
      disruption: {
        type: config.disruptionType,
        durationMinutes: config.delayMinutes,
      },
    }

    setSimulatedRuns((current) => ({
      ...current,
      [runId]: simulatedRun,
    }))
  }

  const updateAgentStatus = (
    shipmentId: string,
    runId: string,
    status: AgentStatus,
  ) => {
    setSimulatedRuns((current) => {
      const run = current[runId]

      if (!run || run.shipmentId !== shipmentId) {
        return current
      }

      return {
        ...current,
        [runId]: {
          ...run,
          agentStatus: status,
          operationalStatus:
            status === "RESOLVED"
              ? "RESOLVED"
              : run.operationalStatus,
        },
      }
    })
  }

  const getRuns = (shipmentId: string) => {
    const simulated = Object.values(simulatedRuns).filter(
      (run) => run.shipmentId === shipmentId,
    )

    if (simulated.length > 0) {
      return simulated
    }

    return baseRuns.filter(
      (run) => run.shipmentId === shipmentId,
    )
  }

  const getRun = (
    shipmentId: string,
    runId: string,
  ) => {
    const simulatedRun = simulatedRuns[runId]

    if (
      simulatedRun &&
      simulatedRun.shipmentId === shipmentId
    ) {
      return simulatedRun
    }

    return baseRuns.find(
      (run) =>
        run.shipmentId === shipmentId &&
        run.runId === runId,
    )
  }

  const value = useMemo(
    () => ({
      simulatedRuns,
      simulateDisruption,
      updateAgentStatus,
      getRuns,
      getRun,
    }),
    [simulatedRuns],
  )

  return (
    <SimulationContext.Provider value={value}>
      {children}
    </SimulationContext.Provider>
  )
}

export function useSimulation() {
  const context = useContext(SimulationContext)

  if (!context) {
    throw new Error(
      "useSimulation must be used within SimulationProvider",
    )
  }

  return context
}