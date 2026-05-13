import { Activity, Bell, LineChart, Newspaper } from "lucide-react";
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
    <main className="min-h-screen bg-background text-foreground">
      <section className="border-b bg-card">
        <div className="mx-auto flex min-h-[72px] w-full max-w-6xl items-center justify-between px-6">
          <div>
            <p className="text-sm font-medium text-muted-foreground">MarketPulse</p>
            <h1 className="text-2xl font-semibold tracking-normal">Workspace</h1>
          </div>
          <Button variant="outline" size="sm">
            <Activity className="h-4 w-4" aria-hidden="true" />
            Ready
          </Button>
        </div>
      </section>

      <section className="mx-auto grid w-full max-w-6xl gap-4 px-6 py-8 md:grid-cols-3">
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
    </main>
  );
}
