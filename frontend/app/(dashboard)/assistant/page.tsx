import { AssistantWorkspace } from "@/features/ai-assistant/components/assistant-workspace";
import { AuthGuard } from "@/shared/components/auth-guard";

export default function AssistantPage() {
  return (
    <AuthGuard>
      <AssistantWorkspace />
    </AuthGuard>
  );
}
