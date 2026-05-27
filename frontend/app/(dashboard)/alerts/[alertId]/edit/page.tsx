import { AlertsEditor } from "@/features/alerts/components/alerts-editor";
import { AuthGuard } from "@/shared/components/auth-guard";

export default async function EditAlertPage({
  params,
}: {
  params: Promise<{ alertId: string }>;
}) {
  const { alertId } = await params;

  return (
    <AuthGuard>
      <AlertsEditor alertId={alertId} />
    </AuthGuard>
  );
}
