import * as React from "react";

import { cn } from "@/shared/lib/utils";

/**
 * MarketPulse mark: an outlined tile with a rising price line whose end point sends out ripples.
 * Keep in sync with `app/icon.svg`.
 */
export function BrandMark({ className }: { className?: string }) {
  const clipId = `${React.useId()}-clip`;

  return (
    <svg
      viewBox="0 0 32 32"
      role="img"
      aria-label="MarketPulse"
      className={cn("size-8 shrink-0", className)}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <clipPath id={clipId}>
          <rect x="1" y="1" width="30" height="30" rx="8" />
        </clipPath>
      </defs>
      <rect
        x="1.2"
        y="1.2"
        width="29.6"
        height="29.6"
        rx="8"
        fill="none"
        stroke="#38bdf8"
        strokeOpacity=".55"
        strokeWidth="1.6"
      />
      <g clipPath={`url(#${clipId})`}>
        <circle cx="24" cy="9" r="9" fill="none" stroke="#38bdf8" strokeOpacity=".25" strokeWidth="1.3" />
        <circle cx="24" cy="9" r="5.5" fill="none" stroke="#38bdf8" strokeOpacity=".5" strokeWidth="1.3" />
      </g>
      <path
        d="M5.5 24l6.5-5.5 5 3 7-12"
        fill="none"
        stroke="#38bdf8"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="24" cy="9" r="2.4" fill="#6ee7b7" />
    </svg>
  );
}
