import { defineConfig } from "orval";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const inputTarget =
  process.env.MARKETPULSE_OPENAPI_TARGET ??
  process.env.MARKETPULSE_OPENAPI_URL ??
  `${apiBaseUrl.replace(/\/+$/, "")}/openapi.json`;

export default defineConfig({
  marketpulse: {
    input: {
      target: inputTarget,
    },
    output: {
      mode: "tags-split",
      target: "src/api/generated/endpoints.ts",
      schemas: "src/api/generated/models",
      client: "react-query",
      clean: true,
      prettier: false,
      override: {
        mutator: {
          path: "./src/api/http-client.ts",
          name: "customFetch",
        },
      },
    },
  },
});
