"use client";

import { Activity, Bell, LineChart, Newspaper, Search } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const navigationItems = [
  { label: "Market data", href: "/market-data", icon: Activity },
  { label: "Watchlists", href: "/", icon: LineChart, disabled: true },
  { label: "News", href: "/", icon: Newspaper, disabled: true },
  { label: "Alerts", href: "/", icon: Bell, disabled: true },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b bg-card">
        <div className="flex min-h-16 items-center justify-between gap-4 px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Activity className="h-5 w-5" aria-hidden="true" />
            </span>
            <span>
              <span className="block text-sm font-medium text-muted-foreground">MarketPulse</span>
              <span className="block text-base font-semibold leading-5">Workspace</span>
            </span>
          </Link>

          <div className="hidden min-w-0 items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm text-muted-foreground sm:flex">
            <Search className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span className="truncate">Stocks, watchlists, news, alerts</span>
          </div>
        </div>
      </header>

      <div className="grid min-h-[calc(100vh-4rem)] md:grid-cols-[248px_minmax(0,1fr)]">
        <aside className="border-b bg-card md:border-b-0 md:border-r">
          <nav className="flex gap-2 overflow-x-auto px-4 py-3 md:flex-col md:px-3 md:py-4">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;

              return (
                <Link
                  key={item.label}
                  href={item.href}
                  aria-disabled={item.disabled}
                  className={cn(
                    "flex h-10 shrink-0 items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    item.disabled && "pointer-events-none opacity-50",
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </aside>

        <main className="min-w-0 bg-background">{children}</main>
      </div>
    </div>
  );
}
