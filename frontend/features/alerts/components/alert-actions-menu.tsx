import Link from "next/link";
import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";

import type { AlertResponse } from "@/src/api/generated/models/alertResponse";
import { Button } from "@/shared/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";

export function AlertActionsMenu({
  alert,
  disabled,
  onDelete,
}: {
  alert: AlertResponse;
  disabled: boolean;
  onDelete: (alert: AlertResponse) => void;
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="size-8 shrink-0"
          disabled={disabled}
          aria-label={`More actions for ${alert.name} alert: ${alert.rule_summary}`}
        >
          <MoreHorizontal className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem asChild>
          <Link href={`/alerts?edit=${encodeURIComponent(alert.id)}`} className="cursor-pointer gap-2">
            <Pencil className="size-4" />
            Edit
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem
          className="cursor-pointer gap-2 text-destructive focus:text-destructive"
          onSelect={() => onDelete(alert)}
        >
          <Trash2 className="size-4" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
