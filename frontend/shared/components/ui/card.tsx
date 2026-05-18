import * as React from "react";

import { cn } from "@/shared/lib/utils";

function Card({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200 bg-white/95 shadow-[0_20px_55px_-28px_rgba(15,23,42,0.45)] backdrop-blur",
        className
      )}
      {...props}
    />
  );
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("p-7 pb-3", className)} {...props} />;
}

function CardTitle({ className, ...props }: React.ComponentProps<"h1">) {
  return <h1 className={cn("text-2xl font-semibold text-slate-900", className)} {...props} />;
}

function CardDescription({ className, ...props }: React.ComponentProps<"p">) {
  return <p className={cn("mt-1 text-sm text-slate-600", className)} {...props} />;
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("p-7 pt-3", className)} {...props} />;
}

export { Card, CardContent, CardDescription, CardHeader, CardTitle };
