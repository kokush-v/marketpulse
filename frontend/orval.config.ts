import { defineConfig } from "orval";

const backendOpenApiUrl =
  process.env.MARKETPULSE_OPENAPI_URL ??
  `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/openapi.json`;

export default defineConfig({
  marketData: {
    input: {
      target: backendOpenApiUrl,
      filters: {
        mode: "include",
        tags: ["Market Data", "market-data", "market_data"],
      },
    },
    output: {
      target: "src/generated/market-data/market-data.ts",
      client: "react-query",
      httpClient: "axios",
      override: {
        mutator: {
          path: "src/lib/api/orval-mutator.ts",
          name: "marketPulseMutator",
        },
        query: {
          useQuery: true,
          version: 5,
          shouldExportQueryKey: true,
        },
      },
    },
  },
});
