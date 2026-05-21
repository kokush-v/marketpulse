"use client";

import { useGetMarketOverviewMarketDataOverviewGet } from "@/src/api/generated/market-data/market-data";

export function useMarketOverview() {
  return useGetMarketOverviewMarketDataOverviewGet(undefined, {
    query: {
      staleTime: 60_000,
      retry: 1,
    },
  });
}
