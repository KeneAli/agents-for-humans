import { useQuery } from "@tanstack/react-query"

import type { Run } from "@/types/run"

const runs: Run[] = [
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

export function useRuns() {
  return useQuery({
    queryKey: ["runs"],
    queryFn: async () => runs,
  })
}