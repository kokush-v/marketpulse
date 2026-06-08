import { AlertsEditor } from "@/features/alerts/components/alerts-editor";
import { AuthGuard } from "@/shared/components/auth-guard";

export default async function NewAlertPage({
  searchParams,
}: {
  searchParams: Promise<{ assetId?: string }>;
}) {
  const { assetId } = await searchParams;

  return (
    <AuthGuard>
      <AlertsEditor initialAssetId={assetId} />
    </AuthGuard>
  );
}
