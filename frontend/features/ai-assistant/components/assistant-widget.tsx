"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { MessageCircle, X } from "lucide-react";
import { usePathname } from "next/navigation";
import * as React from "react";

import { AssistantChat } from "@/features/ai-assistant/components/assistant-chat";
import { Button } from "@/shared/components/ui/button";

export function AssistantWidget() {
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);
  const scrollPositions = React.useRef(new Map<string, number>());
  const activeConversationMemory = React.useRef<string | undefined>(undefined);

  if (pathname === "/assistant") {
    return null;
  }

  return (
    <Dialog.Root modal={false} open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <Button
          type="button"
          size="icon"
          className="fixed bottom-5 right-5 z-40 size-12 rounded-full shadow-lg sm:bottom-6 sm:right-6"
          aria-label={open ? "Close MarketPulse Assistant" : "Open MarketPulse Assistant"}
        >
          <span className="relative flex size-5 items-center justify-center leading-none" aria-hidden="true">
            <MessageCircle
              className={`absolute left-1/2 top-1/2 size-5 -translate-x-1/2 -translate-y-1/2 transition-all duration-200 ease-out ${
                open ? "rotate-90 scale-75 opacity-0" : "rotate-0 scale-100 opacity-100"
              }`}
            />
            <X
              className={`absolute left-1/2 top-1/2 size-5 -translate-x-1/2 -translate-y-1/2 transition-all duration-200 ease-out ${
                open ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-75 opacity-0"
              }`}
            />
          </span>
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Content className="assistant-widget-panel fixed bottom-20 right-2 z-50 flex h-[min(38rem,calc(100svh-6.5rem))] w-[min(34rem,calc(100vw-1rem))] flex-col overflow-hidden rounded-2xl border border-border/70 bg-background shadow-2xl sm:bottom-24 sm:right-6">
          <Dialog.Title className="sr-only">MarketPulse Assistant</Dialog.Title>
          <AssistantChat
            compact
            scrollPositions={scrollPositions.current}
            activeConversationMemory={activeConversationMemory}
          />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
