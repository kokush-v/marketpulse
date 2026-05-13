import axios from "axios";

const authTokenStorageKeys = ["marketpulse.authToken", "marketpulse.auth.bearerToken"];

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = readBearerToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

function readBearerToken() {
  if (typeof window !== "undefined") {
    for (const key of authTokenStorageKeys) {
      const token = readBrowserStorageToken(key);
      if (token) {
        return token;
      }
    }
  }

  return null;
}

function readBrowserStorageToken(key: string) {
  try {
    return (
      window.sessionStorage.getItem(key)?.trim() ||
      window.localStorage.getItem(key)?.trim() ||
      null
    );
  } catch {
    return null;
  }
}
