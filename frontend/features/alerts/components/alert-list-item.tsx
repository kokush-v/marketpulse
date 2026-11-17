import { formatAlertTiming } from "@/features/alerts/lib/alert-builder";
import type { AlertResponse } from "@/src/api/generated/models/alertResponse";

import { AlertActionsMenu } from "./alert-actions-menu";
import { AlertStatusBadge, AlertStatusSwitch } from "./alert-status-controls";
import { ScenarioIcon } from "./alert-visuals";

interface AlertItemProps {
  alert: AlertResponse;
  disabled: boolean;
  onToggleStatus: (alert: AlertResponse) => void;
  onDelete: (alert: AlertResponse) => void;
}

export function AlertRow({ alert, disabled, onToggleStatus, onDelete }: AlertItemProps) {
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <ScenarioIcon scenario={alert.scenario} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{alert.rule_summary}</p>
        <p className="mt-0.5 truncate text-xs text-muted-foreground">{formatAlertTiming(alert)}</p>
      </div>
      <AlertStatusBadge status={alert.status} className="hidden sm:inline-flex" />
      <AlertStatusSwitch alert={alert} disabled={disabled} onToggle={onToggleStatus} />
      <AlertActionsMenu alert={alert} disabled={disabled} onDelete={onDelete} />
    </div>
  );
}

export function AlertCard({ alert, disabled, onToggleStatus, onDelete }: AlertItemProps) {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border/40 bg-card/60 p-4">
      <div className="flex items-start gap-3">
        <ScenarioIcon scenario={alert.scenario} />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold leading-5">{alert.rule_summary}</p>
          <p className="mt-1 text-xs text-muted-foreground">{formatAlertTiming(alert)}</p>
        </div>
        <AlertActionsMenu alert={alert} disabled={disabled} onDelete={onDelete} />
      </div>
      <div className="flex items-center justify-between border-t border-border/30 pt-3">
        <AlertStatusBadge status={alert.status} />
        <AlertStatusSwitch alert={alert} disabled={disabled} onToggle={onToggleStatus} />
      </div>
    </div>
  );
}
