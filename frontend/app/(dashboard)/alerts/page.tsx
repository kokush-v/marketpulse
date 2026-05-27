import { AlertsWorkspace } from "@/features/alerts/components/alerts-workspace";
import { AuthGuard } from "@/shared/components/auth-guard";

export default function AlertsPage() {
  return (
    <AuthGuard>
      <AlertsWorkspace />
    </AuthGuard>
  );
}
