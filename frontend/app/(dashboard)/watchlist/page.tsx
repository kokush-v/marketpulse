import { WatchlistWorkspace } from "@/features/watchlist/components/watchlist-workspace";
import { AuthGuard } from "@/shared/components/auth-guard";

export default function WatchlistPage() {
  return (
    <AuthGuard>
      <WatchlistWorkspace />
    </AuthGuard>
  );
}
