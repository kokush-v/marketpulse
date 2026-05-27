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
      metadata = @snapshot_store.read_metadata
      if snapshot
        if @snapshot_store.snapshot_fresh?(metadata)
          @logger.info("[market-overview] cache hit for fresh reusable snapshot")
          return snapshot
        end

        @logger.info("[market-overview] cache hit for stale reusable snapshot; attempting bounded refresh")
        return @snapshot_refresher.refresh!(reason: "stale_snapshot")
      end

      if metadata
        @logger.info("[market-overview] snapshot metadata exists without payload; attempting bounded refresh")
        return @snapshot_refresher.refresh!(reason: "missing_snapshot_payload")
      end

      @logger.info("[market-overview] cache miss for reusable snapshot; attempting bounded cold start")
      @snapshot_refresher.refresh!(reason: "cold_start")
    end
  end
end
