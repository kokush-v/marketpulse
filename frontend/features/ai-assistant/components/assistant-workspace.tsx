"use client";

import { AppSidebar } from "@/features/market-dashboard/components/app-sidebar";
import { AssistantChat } from "@/features/ai-assistant/components/assistant-chat";
import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from "@/shared/components/ui/breadcrumb";
import { Separator } from "@/shared/components/ui/separator";
import { SidebarInset, SidebarTrigger } from "@/shared/components/ui/sidebar";

export function AssistantWorkspace() {
  return (
    <>
      <AppSidebar />
      <SidebarInset className="h-svh min-h-0 overflow-hidden">
        <header className="flex h-16 shrink-0 items-center gap-2 border-b border-border/40 bg-background/95 px-4 backdrop-blur-sm lg:px-6">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="h-6 bg-border" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage className="text-sm font-semibold">Assistant</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </header>
        <main className="flex min-h-0 flex-1 overflow-hidden bg-background p-4 lg:p-6">
          <AssistantChat showHistory />
        </main>
      </SidebarInset>
    </>
  );
}
