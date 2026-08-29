"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { MessageCircle, X } from "lucide-react";
import { usePathname } from "next/navigation";

import { AssistantChat } from "@/features/ai-assistant/components/assistant-chat";
import { Button } from "@/shared/components/ui/button";

export function AssistantWidget() {
  const pathname = usePathname();

  if (pathname === "/assistant") {
    return null;
  }

  return (
    <Dialog.Root modal={false}>
      <Dialog.Trigger asChild>
        <Button
          type="button"
          size="icon"
          className="fixed bottom-5 right-5 z-40 size-12 rounded-full shadow-lg sm:bottom-6 sm:right-6"
          aria-label="Open MarketPulse Assistant"
        >
          <MessageCircle className="size-5" />
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Content className="assistant-widget-panel fixed bottom-20 right-5 z-50 flex h-[min(38rem,calc(100svh-6.5rem))] w-[calc(100vw-2.5rem)] max-w-sm flex-col overflow-hidden rounded-2xl border border-border/70 bg-background shadow-2xl sm:bottom-24 sm:right-6">
          <Dialog.Title className="sr-only">MarketPulse Assistant</Dialog.Title>
          <Dialog.Close asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-3 top-3 z-10 size-8"
              aria-label="Close MarketPulse Assistant"
            >
              <X className="size-4" />
            </Button>
          </Dialog.Close>
          <AssistantChat compact />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
