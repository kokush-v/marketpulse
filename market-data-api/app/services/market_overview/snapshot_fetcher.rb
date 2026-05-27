require Rails.root.join("app/services/market_overview/snapshot_refresher")
require Rails.root.join("app/services/market_overview/snapshot_store")

module MarketOverview
  class SnapshotFetcher
    def initialize(
      snapshot_store: SnapshotStore.new,
      snapshot_refresher: nil,
      logger: Rails.logger
    )
      @snapshot_store = snapshot_store
      @logger = logger
      @snapshot_refresher = snapshot_refresher || SnapshotRefresher.new(snapshot_store: snapshot_store, logger: logger)
    end

    def fetch!
      snapshot = @snapshot_store.read_snapshot
      if snapshot
        @logger.info("[market-overview] cache hit for reusable snapshot")
        return snapshot
      end

      @logger.info("[market-overview] cache miss for reusable snapshot; attempting bounded cold start")
      @snapshot_refresher.refresh!(reason: "cold_start")
    end
  end
end
