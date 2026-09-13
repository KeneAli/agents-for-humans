import { useQuery } from "@tanstack/react-query"

import { ApiError, getRun } from "@/lib/api"

const terminalStatuses = new Set([
  "COMPLETED",
  "REJECTED",
  "EXPIRED",
  "FAILED",
  "RESUMED_UNCONFIRMED",
])

export function useRun(shipmentId?: string, runId?: string) {
  return useQuery({
    queryKey: ["run", shipmentId, runId],
    queryFn: () => getRun(shipmentId!, runId!),
    enabled: Boolean(shipmentId && runId),
    refetchInterval: (query) => {
      const status = query.state.data?.workflow?.status ?? query.state.data?.approval?.status
      return status && terminalStatuses.has(status) ? false : 1500
    },
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 404) {
        return failureCount < 40
      }
      return failureCount < 2
    },
    retryDelay: 1500,
  })
}
