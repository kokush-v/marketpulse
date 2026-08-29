"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { MessageCircle, Plus, RefreshCw, X } from "lucide-react";
import { usePathname } from "next/navigation";
import * as React from "react";

import { AssistantChat } from "@/features/ai-assistant/components/assistant-chat";
import {
  useCreateConversationAssistantConversationsPost,
  useListConversationsAssistantConversationsGet,
} from "@/src/api/generated/ai-assistant/ai-assistant";
import { Button } from "@/shared/components/ui/button";

export function AssistantWidget() {
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);
  const [showChat, setShowChat] = React.useState(false);
  const scrollPositions = React.useRef(new Map<string, number>());
  const activeConversationMemory = React.useRef<string | undefined>(undefined);

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
    if (!nextOpen) {
      setShowChat(false);
      activeConversationMemory.current = undefined;
    }
  };

  if (pathname === "/assistant") {
    return null;
  }

  return (
    <Dialog.Root modal={false} open={open} onOpenChange={handleOpenChange}>
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
          {showChat ? (
            <AssistantChat
              compact
              scrollPositions={scrollPositions.current}
              activeConversationMemory={activeConversationMemory}
            />
          ) : (
            <WidgetConversationPicker
              activeConversationMemory={activeConversationMemory}
              onSelectConversation={() => setShowChat(true)}
            />
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function WidgetConversationPicker({
  activeConversationMemory,
  onSelectConversation,
}: {
  activeConversationMemory: React.MutableRefObject<string | undefined>;
  onSelectConversation: () => void;
}) {
  const conversationsQuery = useListConversationsAssistantConversationsGet(undefined, {
    query: { retry: 1 },
  });
  const createConversation = useCreateConversationAssistantConversationsPost();
  const [creationError, setCreationError] = React.useState<string>();

  const startConversation = async () => {
    try {
      setCreationError(undefined);
      const conversation = await createConversation.mutateAsync({ data: {} });
      activeConversationMemory.current = conversation.id;
      onSelectConversation();
    } catch {
      setCreationError("We could not create a new conversation. Please try again.");
    }
  };

  const selectConversation = (conversationId: string) => {
    activeConversationMemory.current = conversationId;
    onSelectConversation();
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="shrink-0 border-b border-border/50 px-4 py-3">
        <h2 className="text-sm font-semibold">MarketPulse Assistant</h2>
        <p className="text-xs text-muted-foreground">Choose a conversation or start a new one.</p>
      </div>
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
        <Button
          type="button"
          className="w-full justify-start"
          disabled={createConversation.isPending}
          onClick={() => void startConversation()}
        >
          <Plus className="size-4" /> New conversation
        </Button>
        {creationError ? <p role="alert" className="text-sm text-destructive">{creationError}</p> : null}

        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Recent conversations</p>
          {conversationsQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading conversations…</p>
          ) : conversationsQuery.isError ? (
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>Conversation history is unavailable.</p>
              <Button type="button" variant="outline" size="sm" onClick={() => void conversationsQuery.refetch()}>
                <RefreshCw className="size-3.5" /> Retry
              </Button>
            </div>
          ) : conversationsQuery.data?.items.length ? (
            <div className="space-y-1">
              {conversationsQuery.data.items.map((conversation) => (
                <Button
                  key={conversation.id}
                  type="button"
                  variant="ghost"
                  className="h-auto w-full justify-start px-3 py-2 text-left font-normal"
                  onClick={() => selectConversation(conversation.id)}
                >
                  <span className="truncate">{conversation.title || "New conversation"}</span>
                </Button>
              ))}
            </div>
          ) : (
            <p className="text-sm leading-5 text-muted-foreground">You do not have any conversations yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
