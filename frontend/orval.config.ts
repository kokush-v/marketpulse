import { defineConfig } from "orval";

const inputTarget = process.env.MARKETPULSE_OPENAPI_URL ?? "./marketpulse-openapi.json";

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
      prettier: true,
      override: {
        mutator: {
          path: "./src/api/http-client.ts",
          name: "customFetch",
        },
      },
    },
  },
});
