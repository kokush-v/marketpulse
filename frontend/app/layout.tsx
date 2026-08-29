import "./globals.css";

import type { Metadata } from "next";

import { QueryProvider } from "@/shared/providers/query-provider";

export const metadata: Metadata = {
  title: "MarketPulse",
  description: "Public market dashboard for quotes, movers, and company snapshots.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body>
        <QueryProvider>
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}
