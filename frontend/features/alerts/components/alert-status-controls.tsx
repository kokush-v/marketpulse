import type { AlertResponse } from "@/src/api/generated/models/alertResponse";
import { Badge } from "@/shared/components/ui/badge";
import { Switch } from "@/shared/components/ui/switch";
import { cn } from "@/shared/lib";

export function AlertStatusBadge({ status, className }: { status: AlertResponse["status"]; className?: string }) {
  const isActive = status === "active";

  return (
    <Badge
      variant="outline"
      className={cn(
        "rounded-full px-2.5 py-0.5 capitalize",
        isActive ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400" : "text-muted-foreground",
        className
      )}
    >
      {status}
    </Badge>
  );
}

export function AlertStatusSwitch({
  alert,
  disabled,
  onToggle,
}: {
  alert: AlertResponse;
  disabled: boolean;
  onToggle: (alert: AlertResponse) => void;
}) {
  const isActive = alert.status === "active";

  return (
    <Switch
      checked={isActive}
      disabled={disabled}
      onCheckedChange={() => onToggle(alert)}
      aria-label={`${isActive ? "Pause" : "Resume"} ${alert.name} alert: ${alert.rule_summary}`}
    />
  );
}
