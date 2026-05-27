require Rails.root.join("app/services/market_overview/snapshot_refresher")

namespace :market_overview do
  desc "Refresh the reusable public market overview snapshot"
  task refresh: :environment do
    payload = MarketOverview::SnapshotRefresher.new.refresh!(reason: "scheduled_task")
    puts "Refreshed market overview snapshot generated at #{payload[:generated_at] || payload['generated_at']}"
  end
end
