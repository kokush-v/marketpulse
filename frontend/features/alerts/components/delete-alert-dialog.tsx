import type { AlertResponse } from "@/src/api/generated/models/alertResponse";
import { Button } from "@/shared/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";
import { Spinner } from "@/shared/components/ui/spinner";

export function DeleteAlertDialog({
  alert,
  pending,
  onCancel,
  onConfirm,
}: {
  alert: AlertResponse | null;
  pending: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <Dialog
      open={alert !== null}
      onOpenChange={(open) => {
        if (!open && !pending) {
          onCancel();
        }
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete this alert?</DialogTitle>
          <DialogDescription>
            {alert
              ? `"${alert.rule_summary}" for ${alert.name} will be removed. This cannot be undone.`
              : null}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel} disabled={pending}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={pending}>
            {pending ? <Spinner className="size-4" /> : null}
            Delete alert
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
