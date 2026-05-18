import * as React from "react";

import { cn } from "@/shared/lib/utils";

function Separator({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("h-px w-full bg-slate-200", className)} role="separator" {...props} />;
}

export { Separator };
