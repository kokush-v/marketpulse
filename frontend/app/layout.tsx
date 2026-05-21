import "./globals.css";

import type { Metadata } from "next";

import { AuthSessionSync } from "@/shared/components/auth-session-sync";
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
          <AuthSessionSync />
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}
