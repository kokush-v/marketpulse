import { IntegrationsWorkspace } from "@/features/integrations/components/integrations-workspace";
import { AuthGuard } from "@/shared/components/auth-guard";

export default function IntegrationsPage() {
  return (
    <AuthGuard>
      <IntegrationsWorkspace />
    </AuthGuard>
  );
}
