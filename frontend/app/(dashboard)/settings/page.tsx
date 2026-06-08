import { SettingsWorkspace } from "@/features/settings/components/settings-workspace";
import { AuthGuard } from "@/shared/components/auth-guard";

export default function SettingsPage() {
  return (
    <AuthGuard>
      <SettingsWorkspace />
    </AuthGuard>
  );
}
