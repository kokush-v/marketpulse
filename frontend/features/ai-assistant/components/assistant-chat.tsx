"use client";

import * as React from "react";
import { ArrowDown, Bot, Check, MessageCircle, Pencil, Plus, RefreshCw, RotateCcw, Send, Trash2, X } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  getGetConversationAssistantConversationsConversationIdGetQueryKey,
  getListConversationsAssistantConversationsGetQueryKey,
  useCreateConversationAssistantConversationsPost,
  useDeleteConversationAssistantConversationsConversationIdDelete,
  useGetConversationAssistantConversationsConversationIdGet,
  useListConversationsAssistantConversationsGet,
  useSendMessageAssistantConversationsConversationIdMessagesPost,
  useUpdateConversationTitleAssistantConversationsConversationIdPatch,
} from "@/src/api/generated/ai-assistant/ai-assistant";
import type { AssistantConversationResponse } from "@/src/api/generated/models/assistantConversationResponse";
import { ApiRequestError } from "@/src/api/http-client";
import { Button } from "@/shared/components/ui/button";
import { ScrollArea } from "@/shared/components/ui/scroll-area";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/shared/components/ui/context-menu";
import { cn } from "@/shared/lib/utils";
import { MessageSources } from "./message-sources";
import { PendingActionCard } from "./pending-action-card";
import { PriceChartCard } from "./price-chart-card";

type AssistantChatProps = {
  showHistory?: boolean;
  compact?: boolean;
  scrollPositions?: Map<string, number>;
  activeConversationMemory?: React.MutableRefObject<string | undefined>;
};

const EMPTY_SUGGESTED_REPLIES: string[] = [];

export function getSuggestedReplyVisibleMessageIds(
  messages: AssistantConversationResponse["messages"],
): Set<string> {
  const visibleMessageIds = new Set<string>();
  let hasLaterUserMessage = false;

  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (message.role === "user") {
      hasLaterUserMessage = true;
      continue;
    }

    if (!hasLaterUserMessage && message.suggested_replies?.length) {
      visibleMessageIds.add(message.id);
    }
  }

  return visibleMessageIds;
}

export function AssistantChat({
  showHistory = false,
  compact = false,
  scrollPositions: providedScrollPositions,
  activeConversationMemory,
}: AssistantChatProps) {
  const queryClient = useQueryClient();
  const internalScrollPositions = React.useRef(new Map<string, number>());
  const scrollPositions = providedScrollPositions ?? internalScrollPositions.current;
  const [activeConversationId, setActiveConversationIdState] = React.useState<string | undefined>(
    activeConversationMemory?.current,
  );
  const [pendingMessage, setPendingMessage] = React.useState<string>();
  const [failedMessage, setFailedMessage] = React.useState<FailedMessage>();
  const [historyError, setHistoryError] = React.useState<string>();
  const [editingConversationId, setEditingConversationId] = React.useState<string>();
  const [titleDraft, setTitleDraft] = React.useState("");
  const [deletingConversationId, setDeletingConversationId] = React.useState<string>();
  const [hiddenSuggestedReplyMessageIds, setHiddenSuggestedReplyMessageIds] = React.useState<Set<string>>(
    () => new Set(),
  );
  const [hasNewMessagesBelow, setHasNewMessagesBelow] = React.useState(false);
  const messagesViewportRef = React.useRef<HTMLDivElement>(null);
  const activeConversationIdRef = React.useRef<string | undefined>(undefined);
  const renderedConversationIdRef = React.useRef<string | undefined>(undefined);
  const renderedMessageCountRef = React.useRef(0);
  const isNearBottomRef = React.useRef(true);
  const forceScrollToBottomRef = React.useRef(false);

  const setActiveConversationId = React.useCallback(
    (conversationId: string | undefined) => {
      if (activeConversationMemory) {
        activeConversationMemory.current = conversationId;
      }
      setActiveConversationIdState(conversationId);
    },
    [activeConversationMemory],
  );

  const conversationsQuery = useListConversationsAssistantConversationsGet(undefined, {
    query: { staleTime: 30_000, retry: 1 },
  });
  const conversationQuery = useGetConversationAssistantConversationsConversationIdGet(
    activeConversationId ?? "",
    undefined,
    { query: { enabled: Boolean(activeConversationId), retry: 1 } },
  );
  const createConversation = useCreateConversationAssistantConversationsPost();
  const sendMessage = useSendMessageAssistantConversationsConversationIdMessagesPost();
  const updateConversationTitle = useUpdateConversationTitleAssistantConversationsConversationIdPatch();
  const deleteConversation = useDeleteConversationAssistantConversationsConversationIdDelete();

  React.useEffect(() => {
    if (activeConversationId || !conversationsQuery.data?.items.length) {
      return;
    }

    setActiveConversationId(conversationsQuery.data.items[0].id);
  }, [activeConversationId, conversationsQuery.data]);

  const setConversation = React.useCallback(
    (conversation: AssistantConversationResponse) => {
      queryClient.setQueryData(
        getGetConversationAssistantConversationsConversationIdGetQueryKey(conversation.id),
        conversation,
      );
      setActiveConversationId(conversation.id);
    },
    [queryClient],
  );

  const startConversation = React.useCallback(async () => {
    const conversation = await createConversation.mutateAsync({ data: {} });
    setConversation(conversation);
    await queryClient.invalidateQueries({
      queryKey: getListConversationsAssistantConversationsGetQueryKey(),
    });
  }, [createConversation, queryClient, setConversation]);

  const sendContent = React.useCallback(async (value: string) => {
    const content = value.trim();
    if (!content || sendMessage.isPending || createConversation.isPending) {
      return;
    }

    setFailedMessage(undefined);
    forceScrollToBottomRef.current = true;
    setPendingMessage(content);

    try {
      let conversationId = activeConversationId;
      if (!conversationId) {
        const conversation = await createConversation.mutateAsync({ data: {} });
        setConversation(conversation);
        conversationId = conversation.id;
      }

      const conversation = await sendMessage.mutateAsync({
        conversationId,
        data: { content },
      });
      setConversation(conversation);
      await queryClient.invalidateQueries({
        queryKey: getListConversationsAssistantConversationsGetQueryKey(),
      });
    } catch (error) {
      setFailedMessage({
        content,
        error: getErrorDetails(error, "We could not send that message. Please try again."),
      });
    } finally {
      setPendingMessage(undefined);
    }
  }, [
    activeConversationId,
    createConversation,
    queryClient,
    sendMessage,
    setConversation,
  ]);

  const retryFailedMessage = React.useCallback(() => {
    if (failedMessage) {
      void sendContent(failedMessage.content);
    }
  }, [failedMessage, sendContent]);

  const selectSuggestedReply = React.useCallback(
    (messageId: string, reply: string) => {
      setHiddenSuggestedReplyMessageIds((hiddenMessageIds) => {
        const nextHiddenMessageIds = new Set(hiddenMessageIds);
        nextHiddenMessageIds.add(messageId);
        return nextHiddenMessageIds;
      });
      void sendContent(reply);
    },
    [sendContent],
  );

  const startRenaming = (conversationId: string, title: string | null | undefined) => {
    setHistoryError(undefined);
    setDeletingConversationId(undefined);
    setEditingConversationId(conversationId);
    setTitleDraft(title || "");
  };

  const saveTitle = async (conversationId: string) => {
    const title = titleDraft.trim();
    if (!title) {
      setHistoryError("Conversation title must not be blank.");
      return;
    }

    try {
      setHistoryError(undefined);
      const conversation = await updateConversationTitle.mutateAsync({
        conversationId,
        data: { title },
      });
      queryClient.setQueryData(
        getGetConversationAssistantConversationsConversationIdGetQueryKey(conversation.id),
        conversation,
      );
      await queryClient.invalidateQueries({
        queryKey: getListConversationsAssistantConversationsGetQueryKey(),
      });
      setEditingConversationId(undefined);
    } catch (error) {
      setHistoryError(getErrorDetails(error, "We could not rename that conversation.").message);
    }
  };

  const confirmDelete = async (conversationId: string) => {
    try {
      setHistoryError(undefined);
      await deleteConversation.mutateAsync({ conversationId });
      queryClient.removeQueries({
        queryKey: getGetConversationAssistantConversationsConversationIdGetQueryKey(conversationId),
      });
      await queryClient.invalidateQueries({
        queryKey: getListConversationsAssistantConversationsGetQueryKey(),
      });
      if (conversationId === activeConversationId) {
        const conversations = queryClient.getQueryData<{ items: { id: string }[] }>(
          getListConversationsAssistantConversationsGetQueryKey(),
        );
        setActiveConversationId(conversations?.items[0]?.id);
      }
      setDeletingConversationId(undefined);
    } catch (error) {
      setHistoryError(getErrorDetails(error, "We could not delete that conversation.").message);
    }
  };

  const conversation = conversationQuery.data;
  const messages = conversation?.messages ?? [];
  const visibleSuggestedReplyMessageIds = React.useMemo(
    () => getSuggestedReplyVisibleMessageIds(messages),
    [messages],
  );
  const isBusy = createConversation.isPending || sendMessage.isPending;
  const renderedMessageCount = messages.length + (pendingMessage ? 1 : 0) + (failedMessage ? 1 : 0);

  activeConversationIdRef.current = activeConversationId;

  const updateScrollPosition = React.useCallback(() => {
    const viewport = messagesViewportRef.current;
    if (!viewport || !activeConversationId) {
      return;
    }

    scrollPositions.set(activeConversationId, viewport.scrollTop);
    const distanceFromBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
    const isNearBottom = distanceFromBottom <= 80;
    isNearBottomRef.current = isNearBottom;
    if (isNearBottom) {
      setHasNewMessagesBelow(false);
    }
  }, [activeConversationId, scrollPositions]);

  const scrollToBottom = React.useCallback((behavior: ScrollBehavior = "smooth") => {
    const viewport = messagesViewportRef.current;
    if (!viewport) {
      return;
    }

    viewport.scrollTo({ top: viewport.scrollHeight, behavior });
    isNearBottomRef.current = true;
    setHasNewMessagesBelow(false);
    if (activeConversationId) {
      scrollPositions.set(activeConversationId, viewport.scrollHeight);
    }
  }, [activeConversationId, scrollPositions]);

  React.useLayoutEffect(() => {
    const viewport = messagesViewportRef.current;
    if (!viewport || !activeConversationId || conversation?.id !== activeConversationId) {
      return;
    }

    const conversationChanged = renderedConversationIdRef.current !== activeConversationId;
    if (conversationChanged) {
      renderedConversationIdRef.current = activeConversationId;
      renderedMessageCountRef.current = renderedMessageCount;
      const savedPosition = scrollPositions.get(activeConversationId);
      viewport.scrollTop = savedPosition ?? viewport.scrollHeight;
      const distanceFromBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
      isNearBottomRef.current = distanceFromBottom <= 80;
      forceScrollToBottomRef.current = false;
      setHasNewMessagesBelow(false);
      return;
    }

    if (renderedMessageCount > renderedMessageCountRef.current) {
      if (forceScrollToBottomRef.current || isNearBottomRef.current) {
        scrollToBottom("smooth");
      } else {
        setHasNewMessagesBelow(true);
      }
    }

    renderedMessageCountRef.current = renderedMessageCount;
    forceScrollToBottomRef.current = false;
  }, [activeConversationId, conversation?.id, renderedMessageCount, scrollPositions, scrollToBottom]);

  React.useEffect(() => {
    const viewportRef = messagesViewportRef;
    return () => {
      const viewport = viewportRef.current;
      const conversationId = activeConversationIdRef.current;
      if (viewport && conversationId) {
        scrollPositions.set(conversationId, viewport.scrollTop);
      }
    };
  }, [scrollPositions]);

  return (
    <div className={cn("flex min-h-0 min-w-0 flex-1 overflow-hidden", showHistory && "rounded-2xl border border-border/50 bg-card") }>
      {showHistory ? (
        <aside className="hidden w-64 shrink-0 border-r border-border/50 bg-muted/20 p-3 md:flex md:flex-col">
          <Button type="button" className="mb-3 w-full justify-start" onClick={() => void startConversation()} disabled={isBusy}>
            <Plus className="size-4" />
            New conversation
          </Button>
          <ScrollArea className="min-h-0 flex-1 pr-2">
            {conversationsQuery.isLoading ? (
              <p className="px-2 py-3 text-sm text-muted-foreground">Loading conversations…</p>
            ) : conversationsQuery.isError ? (
              <div className="space-y-2 px-2 py-3 text-sm text-muted-foreground">
                <p>Conversation history is unavailable.</p>
                <Button type="button" variant="outline" size="sm" onClick={() => void conversationsQuery.refetch()}>
                  <RefreshCw className="size-3.5" /> Retry
                </Button>
              </div>
            ) : conversationsQuery.data?.items.length ? (
              <div className="space-y-1">
                {historyError ? <p role="alert" className="px-2 text-xs text-destructive">{historyError}</p> : null}
                {conversationsQuery.data.items.map((item) => (
                  <div key={item.id}>
                    {editingConversationId === item.id ? (
                      <form
                        className="space-y-2 rounded-lg bg-accent/60 p-2"
                        onSubmit={(event) => {
                          event.preventDefault();
                          void saveTitle(item.id);
                        }}
                      >
                        <input
                          autoFocus
                          value={titleDraft}
                          maxLength={200}
                          onChange={(event) => setTitleDraft(event.target.value)}
                          className="h-8 w-full rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          aria-label="Conversation title"
                        />
                        <div className="flex gap-1">
                          <Button type="submit" size="sm" className="h-7 flex-1" disabled={updateConversationTitle.isPending}>
                            <Check /> Save
                          </Button>
                          <Button type="button" size="sm" variant="ghost" className="h-7" onClick={() => setEditingConversationId(undefined)} disabled={updateConversationTitle.isPending}>
                            <X /> Cancel
                          </Button>
                        </div>
                      </form>
                    ) : deletingConversationId === item.id ? (
                      <div className="space-y-2 rounded-lg border border-destructive/30 bg-destructive/10 p-2 text-xs">
                        <p>Delete this conversation?</p>
                        <div className="flex gap-1">
                          <Button type="button" size="sm" variant="destructive" className="h-7 flex-1" onClick={() => void confirmDelete(item.id)} disabled={deleteConversation.isPending}>
                            <Trash2 /> Delete
                          </Button>
                          <Button type="button" size="sm" variant="ghost" className="h-7" onClick={() => setDeletingConversationId(undefined)} disabled={deleteConversation.isPending}>
                            <X /> Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <ContextMenu>
                        <ContextMenuTrigger asChild>
                          <button
                            type="button"
                            onClick={() => setActiveConversationId(item.id)}
                            className={cn(
                              "w-full rounded-lg px-3 py-2 text-left text-sm transition hover:bg-accent",
                              item.id === activeConversationId && "bg-accent font-medium text-accent-foreground",
                            )}
                          >
                            <span className="block truncate">{item.title || "New conversation"}</span>
                          </button>
                        </ContextMenuTrigger>
                        <ContextMenuContent>
                          <ContextMenuItem onSelect={() => startRenaming(item.id, item.title)}>
                            <Pencil /> Rename
                          </ContextMenuItem>
                          <ContextMenuItem className="text-destructive focus:text-destructive" onSelect={() => {
                            setHistoryError(undefined);
                            setEditingConversationId(undefined);
                            setDeletingConversationId(item.id);
                          }}>
                            <Trash2 /> Delete
                          </ContextMenuItem>
                        </ContextMenuContent>
                      </ContextMenu>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="px-2 py-3 text-sm leading-5 text-muted-foreground">Your conversations will appear here.</p>
            )}
          </ScrollArea>
        </aside>
      ) : null}

      <section className="relative flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="shrink-0 border-b border-border/50 px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="flex size-8 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Bot className="size-4" />
            </span>
            <div>
              <h2 className="text-sm font-semibold">MarketPulse Assistant</h2>
              <p className="text-xs text-muted-foreground">Ask about crypto and your workspace.</p>
            </div>
          </div>
        </div>

        <ScrollArea
          className={cn("min-h-0 min-w-0 flex-1 overflow-x-hidden", compact ? "px-3" : "px-6 sm:px-8 lg:px-10")}
          viewportRef={messagesViewportRef}
          onViewportScroll={updateScrollPosition}
          viewportClassName="min-w-0 max-w-full [&>div]:!block [&>div]:w-full [&>div]:min-w-0 [&>div]:max-w-full"
        >
          <div className={cn("flex min-h-full min-w-0 w-full max-w-full flex-col justify-end gap-4 overflow-x-hidden", compact ? "py-4" : "py-5")}>
            {conversationQuery.isLoading ? (
              <p className="text-center text-sm text-muted-foreground">Loading conversation…</p>
            ) : conversationQuery.isError ? (
              <ChatError
                {...getErrorDetails(conversationQuery.error, "Conversation unavailable.")}
                onRetry={() => void conversationQuery.refetch()}
              />
            ) : messages.length === 0 && !pendingMessage && !failedMessage ? (
              <div className="my-auto flex flex-col items-center text-center">
                <span className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary"><MessageCircle className="size-5" /></span>
                <h3 className="mt-4 font-semibold">How can I help?</h3>
                <p className="mt-1 max-w-sm text-sm leading-6 text-muted-foreground">Start a conversation about a coin or ask the assistant to help with your MarketPulse workspace.</p>
              </div>
            ) : (
              messages.map((message, index) => (
                <ChatMessage
                  key={message.id}
                  messageId={message.id}
                  compact={compact}
                  role={message.role}
                  content={message.content}
                  chartPayload={message.chart_payload}
                  pendingAction={message.pending_action}
                  sources={message.sources}
                  suggestedReplies={
                    hiddenSuggestedReplyMessageIds.has(message.id) || !visibleSuggestedReplyMessageIds.has(message.id)
                      ? EMPTY_SUGGESTED_REPLIES
                      : message.suggested_replies
                  }
                  onSuggestedReply={selectSuggestedReply}
                  suggestionsDisabled={isBusy}
                  animationDelay={Math.min(index, 8) * 35}
                />
              ))
            )}
            {pendingMessage ? <ChatMessage compact={compact} role="user" content={pendingMessage} /> : null}
            {failedMessage ? (
              <ChatMessage
                compact={compact}
                role="user"
                content={failedMessage.content}
                errorMessage={failedMessage.error.message}
                onRetry={retryFailedMessage}
                retryDisabled={isBusy}
              />
            ) : null}
            {isBusy ? <p className="text-sm text-muted-foreground">Assistant is thinking…</p> : null}
          </div>
        </ScrollArea>

        {hasNewMessagesBelow ? (
          <Button
            type="button"
            size="sm"
            variant="secondary"
            className="absolute bottom-20 left-1/2 z-10 -translate-x-1/2 rounded-full border border-border/70 shadow-lg"
            onClick={() => scrollToBottom("smooth")}
          >
            <ArrowDown className="size-3.5" /> New message
          </Button>
        ) : null}

        <AssistantComposer compact={compact} isBusy={isBusy} onSend={sendContent} />
      </section>
    </div>
  );
}

const AssistantComposer = React.memo(function AssistantComposer({
  compact,
  isBusy,
  onSend,
}: {
  compact: boolean;
  isBusy: boolean;
  onSend: (content: string) => Promise<void>;
}) {
  const [draft, setDraft] = React.useState("");

  const submitMessage = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const content = draft.trim();
    if (!content || isBusy) {
      return;
    }

    setDraft("");
    void onSend(content);
  };

  return (
    <div className={cn("shrink-0 border-t border-border/50", compact ? "p-2.5" : "p-4")}>
      <form onSubmit={submitMessage} className="flex gap-2">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask about a coin…"
          maxLength={4000}
          disabled={isBusy}
          className="h-10 min-w-0 flex-1 rounded-md border border-input bg-background px-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
          aria-label="Message the assistant"
        />
        <Button type="submit" size="icon" disabled={isBusy || !draft.trim()} aria-label="Send message">
          <Send className="size-4" />
        </Button>
      </form>
    </div>
  );
});

export const ChatMessage = React.memo(function ChatMessage({
  messageId,
  compact = false,
  role,
  content,
  suggestedReplies = [],
  chartPayload,
  pendingAction,
  sources,
  errorMessage,
  onSuggestedReply,
  onRetry,
  suggestionsDisabled = false,
  retryDisabled = false,
  animationDelay = 0,
}: {
  messageId?: string;
  compact?: boolean;
  role: "user" | "assistant";
  content: string;
  suggestedReplies?: string[];
  chartPayload?: AssistantConversationResponse["messages"][number]["chart_payload"];
  pendingAction?: AssistantConversationResponse["messages"][number]["pending_action"];
  sources?: AssistantConversationResponse["messages"][number]["sources"];
  errorMessage?: string;
  onSuggestedReply?: (messageId: string, reply: string) => void;
  onRetry?: () => void;
  suggestionsDisabled?: boolean;
  retryDisabled?: boolean;
  animationDelay?: number;
}) {
  const isUser = role === "user";
  return (
    <div
      className={cn("assistant-message-in flex", isUser && "justify-end")}
      style={{ animationDelay: `${animationDelay}ms` }}
    >
      <div
        className={cn(
          "min-w-0",
          compact ? "max-w-[76%]" : "max-w-[85%]",
          !isUser && (compact ? "max-w-[88%]" : "max-w-full"),
          isUser && !compact && "sm:max-w-[85%]",
        )}
      >
        <div
          className={cn(
            "break-words text-sm leading-6",
            isUser
              ? "whitespace-pre-wrap [overflow-wrap:anywhere] rounded-2xl rounded-tr-sm bg-primary px-3 py-2 text-primary-foreground"
              : "py-1 text-foreground",
          )}
        >
          {isUser ? content : <AssistantMarkdown content={content} />}
        </div>
        {isUser && errorMessage && onRetry ? (
          <div className="mt-2 flex flex-col items-end gap-1">
            <p role="alert" className="text-right text-xs text-destructive">{errorMessage}</p>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 gap-1 px-2 text-xs"
              disabled={retryDisabled}
              onClick={onRetry}
            >
              <RotateCcw className="size-3.5" /> Retry
            </Button>
          </div>
        ) : null}
        {!isUser && pendingAction ? (
          <PendingActionCard
            action={pendingAction}
          />
        ) : null}
        {!isUser && chartPayload ? <PriceChartCard chart={chartPayload} /> : null}
        {!isUser && sources?.length ? <MessageSources sources={sources} /> : null}
        {!isUser && messageId && suggestedReplies.length > 0 && onSuggestedReply ? (
          <div className="mt-2 flex flex-wrap gap-2">
            {suggestedReplies.map((reply) => (
              <Button
                key={reply}
                type="button"
                variant="outline"
                size="sm"
                disabled={suggestionsDisabled}
                className="h-auto min-h-8 max-w-full whitespace-normal rounded-full px-3 py-1.5 text-left text-xs leading-4"
                onClick={() => onSuggestedReply(messageId, reply)}
              >
                {reply}
              </Button>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
});

function AssistantMarkdown({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ children }) => <h1 className="mt-5 text-xl font-semibold tracking-tight first:mt-0">{children}</h1>,
        h2: ({ children }) => <h2 className="mt-5 text-lg font-semibold tracking-tight first:mt-0">{children}</h2>,
        h3: ({ children }) => <h3 className="mt-4 text-base font-semibold first:mt-0">{children}</h3>,
        a: ({ children, href }) => (
          <a
            href={href}
            target="_blank"
            rel="noreferrer"
            className="font-medium text-primary underline underline-offset-2"
          >
            {children}
          </a>
        ),
        p: ({ children }) => <p className="mt-3 max-w-full break-words first:mt-0">{children}</p>,
        ul: ({ children }) => <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>,
        ol: ({ children }) => <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>,
        li: ({ children }) => <li>{children}</li>,
        blockquote: ({ children }) => (
          <blockquote className="my-3 border-l-2 border-primary/50 pl-3 text-muted-foreground">
            {children}
          </blockquote>
        ),
        code: ({ children, className }) => (
          <code
            className={cn(
              "font-mono text-[0.85em]",
              className
                ? "text-inherit"
                : "break-all rounded-md border border-border/60 bg-muted px-1.5 py-0.5 text-foreground",
            )}
          >
            {children}
          </code>
        ),
        pre: ({ children }) => (
          <pre className="my-3 max-w-full overflow-x-auto rounded-xl border border-border/70 bg-zinc-950 p-4 text-xs leading-5 text-zinc-100 shadow-sm dark:bg-black">
            {children}
          </pre>
        ),
        table: ({ children }) => (
          <div className="my-3 max-w-full overflow-x-auto rounded-xl border border-border/70 bg-background shadow-sm">
            <table className="w-full table-fixed border-collapse text-left text-xs leading-5">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-muted/70 text-foreground">{children}</thead>,
        th: ({ children }) => <th className="break-words border-b border-border px-3 py-2 text-xs font-semibold">{children}</th>,
        td: ({ children }) => <td className="break-words border-b border-border/60 px-3 py-2 align-top last:border-b-0">{children}</td>,
        tr: ({ children }) => <tr className="last:[&>td]:border-b-0">{children}</tr>,
        hr: () => <hr className="my-4 border-border/70" />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

type ChatErrorDetails = {
  message: string;
  retryable: boolean;
};

type FailedMessage = {
  content: string;
  error: ChatErrorDetails;
};

function ChatError({
  message,
  retryable,
  onRetry,
}: ChatErrorDetails & { onRetry: () => void }) {
  return (
    <div role="alert" className="my-auto rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-center">
      <p className="text-sm text-destructive">{message}</p>
      {retryable ? (
        <Button type="button" variant="outline" size="sm" className="mt-3" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}

function getErrorDetails(error: unknown, fallback: string): ChatErrorDetails {
  if (error instanceof ApiRequestError) {
    return { message: error.message || fallback, retryable: error.retryable };
  }
  return { message: error instanceof Error && error.message ? error.message : fallback, retryable: false };
}
