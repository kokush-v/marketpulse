import "./globals.css";

import type { Metadata } from "next";

import { AuthSessionSync } from "@/shared/components/auth-session-sync";
import { QueryProvider } from "@/shared/providers/query-provider";

export const metadata: Metadata = {
  title: "MarketPulse",
  description: "MarketPulse frontend foundation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <AuthSessionSync />
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}
