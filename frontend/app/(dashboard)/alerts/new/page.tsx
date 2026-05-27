import { AlertsEditor } from "@/features/alerts/components/alerts-editor";
import { AuthGuard } from "@/shared/components/auth-guard";

export default function NewAlertPage() {
  return (
    <AuthGuard>
      <AlertsEditor />
    </AuthGuard>
  );
}
