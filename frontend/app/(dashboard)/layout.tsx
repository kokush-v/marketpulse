import type { ReactNode } from "react";

import { SidebarProvider } from "@/shared/components/ui/sidebar";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-background text-foreground">{children}</div>
    </SidebarProvider>
  );
}
