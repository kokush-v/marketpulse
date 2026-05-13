import "./globals.css";

import type { Metadata } from "next";

import { QueryProvider } from "@/shared/providers/query-provider";

export const metadata: Metadata = {
  title: "MarketPulse",
  description: "MarketPulse frontend foundation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
