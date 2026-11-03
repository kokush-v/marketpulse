"use client";

import { AlertTriangle, ExternalLink } from "lucide-react";

import type { AssistantMessageSourceResponse } from "@/src/api/generated/models/assistantMessageSourceResponse";

type MessageSourcesProps = {
  sources: AssistantMessageSourceResponse[];
};

export function MessageSources({ sources }: MessageSourcesProps) {
  if (sources.length === 0) {
    return null;
  }
  return (
    <section aria-label="Sources" className="mt-2 rounded-lg border bg-muted/30 px-3 py-2 text-xs">
      <h4 className="font-medium text-muted-foreground">Sources</h4>
      <ul className="mt-1 space-y-1">
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
