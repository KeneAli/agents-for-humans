import { useQuery } from "@tanstack/react-query"

import { getShipments } from "@/lib/api"

export function useShipments() {
  return useQuery({
    queryKey: ["shipments"],
    queryFn: getShipments,
    staleTime: 5 * 60 * 1000,
  })
}
