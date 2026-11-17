import { AlertsWorkspace, type AlertPanelTarget } from "@/features/alerts/components/alerts-workspace";
import { AuthGuard } from "@/shared/components/auth-guard";

function resolvePanel(params: { new?: string; edit?: string; assetId?: string }): AlertPanelTarget | null {
  if (params.edit) {
    return { mode: "edit", alertId: params.edit };
  }

  if (params.new !== undefined) {
    return { mode: "new", assetId: params.assetId };
  }

  return null;
}

export default async function AlertsPage({
  searchParams,
}: {
  searchParams: Promise<{ new?: string; edit?: string; assetId?: string }>;
}) {
  const panel = resolvePanel(await searchParams);

  return (
    <AuthGuard>
      <AlertsWorkspace panel={panel} />
    </AuthGuard>
  );
}
