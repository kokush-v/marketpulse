import { Activity, BarChart3, Bell, LineChart, Newspaper } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

const workspaceItems = [
  { label: "Market data", icon: Activity, href: "/market-data" },
  { label: "Watchlists", icon: LineChart },
  { label: "News", icon: Newspaper },
  { label: "Alerts", icon: Bell },
];

export default function Home() {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:py-8">
      <section className="flex flex-col gap-4 border-b pb-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Overview</p>
          <h1 className="text-2xl font-semibold tracking-normal">Workspace</h1>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link href="/market-data">
            <BarChart3 className="h-4 w-4" aria-hidden="true" />
            Open market data
          </Link>
        </Button>
      </section>

      <section className="grid gap-4 py-6 md:grid-cols-3">
        {workspaceItems.map((item) => (
          <div key={item.label} className="rounded-lg border bg-card p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <item.icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <h2 className="text-base font-semibold">{item.label}</h2>
            </div>
            {item.href ? (
              <Button asChild variant="outline" size="sm" className="mt-5">
                <Link href={item.href}>Open</Link>
              </Button>
            ) : null}
          </div>
        ))}
      </section>
    </div>
  );
}
