"use client";

import * as React from "react";
import { AlertTriangle, ChevronDown, ExternalLink } from "lucide-react";

import { cn } from "@/shared/lib/utils";
import type { AssistantMessageSourceResponse } from "@/src/api/generated/models/assistantMessageSourceResponse";

type MessageSourcesProps = {
  sources: AssistantMessageSourceResponse[];
};

export function MessageSources({ sources }: MessageSourcesProps) {
  const [expanded, setExpanded] = React.useState(false);
  const listId = React.useId();
  if (sources.length === 0) {
    return null;
  }
  const labels = [...new Set(sources.map((source) => source.label))];
  return (
    <section aria-label="Sources" className="mt-2 rounded-lg border bg-muted/30 px-3 py-2 text-xs">
      <button
        type="button"
        aria-expanded={expanded}
        aria-controls={listId}
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full min-w-0 items-center gap-1.5 text-left text-muted-foreground hover:text-foreground"
      >
        <h4 className="shrink-0 font-medium">Sources</h4>
        {expanded ? null : (
          <span className="min-w-0 truncate">
            <span aria-hidden="true"> · </span>
            {labels.join(" · ")}
          </span>
        )}
        <span className="shrink-0 tabular-nums">({sources.length})</span>
        <ChevronDown
          className={cn("ml-auto size-3.5 shrink-0 transition-transform", expanded && "rotate-180")}
          aria-hidden="true"
        />
      </button>
      {expanded ? (
        <ul id={listId} className="mt-1 space-y-1">
          {sources.map((source) => (
            <li key={`${source.kind}-${source.url ?? source.title}`} className="leading-5">
              <span className="font-medium">{source.label}</span>
              <span className="text-muted-foreground"> · </span>
              {source.kind === "news" && source.url ? (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 underline-offset-2 hover:underline [overflow-wrap:anywhere]"
                >
                  {source.title}
                  <ExternalLink className="size-3 shrink-0" aria-hidden="true" />
                </a>
              ) : (
                <span>{source.title}</span>
              )}
              {source.updated_at ? (
                <span className="text-muted-foreground"> · {formatSourceTime(source.updated_at)}</span>
              ) : null}
              {source.stale ? (
                <span className="ml-1 inline-flex items-center gap-1 text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="size-3" aria-hidden="true" />
                  May be outdated
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function formatSourceTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}
