require Rails.root.join("app/services/coingecko/client")
require Rails.root.join("app/services/market_overview/overview_builder")
require Rails.root.join("app/services/market_overview/snapshot_store")

module MarketOverview
  class SnapshotRefresher
    def initialize(
      snapshot_store: SnapshotStore.new,
      logger: Rails.logger,
      builder_factory: nil
    )
      @snapshot_store = snapshot_store
      @logger = logger
      @builder_factory = builder_factory || default_builder_factory
    end

    def refresh!(reason: "scheduled")
      existing_snapshot = @snapshot_store.read_snapshot
      started_at = Process.clock_gettime(Process::CLOCK_MONOTONIC)

      refreshed_snapshot = @snapshot_store.with_refresh_lock do
        payload = @builder_factory.call.call
        @snapshot_store.write_snapshot(
          payload,
          metadata: {
            "refresh_reason" => reason,
            "refreshed_at" => Time.now.utc.iso8601
          }
        )
      end

      if refreshed_snapshot == false
        @logger.info("[market-overview] refresh skipped because another refresh is already in progress")
        return existing_snapshot if existing_snapshot

        raise CoinGecko::ProviderError, "Market overview refresh already in progress"
      end

      duration_ms = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - started_at) * 1000).round
      @logger.info("[market-overview] refresh succeeded reason=#{reason} duration_ms=#{duration_ms}")
      refreshed_snapshot
    rescue CoinGecko::Error => error
      handle_refresh_failure(error, existing_snapshot, reason: reason)
    rescue StandardError => error
      handle_refresh_failure(error, existing_snapshot, reason: reason)
    end

    private

    def default_builder_factory
      lambda do
        OverviewBuilder.new(
          client: Rails.application.config.x.market_data_client_factory.call,
          ranked_asset_ids: Rails.application.config.x.market_overview_ranked_asset_ids,
          ranking_basis: Rails.application.config.x.market_overview_ranking_basis,
          detail_threads: Rails.application.config.x.market_overview_detail_threads,
          logger: @logger
        )
      end
    end

    def handle_refresh_failure(error, existing_snapshot, reason:)
      @logger.error("[market-overview] refresh failed reason=#{reason} error=#{error.class}: #{error.message}")
      return existing_snapshot if existing_snapshot

      raise error
    end
  end
end
