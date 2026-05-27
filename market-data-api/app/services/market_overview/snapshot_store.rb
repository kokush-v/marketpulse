require "securerandom"

module MarketOverview
  class SnapshotStore
    def initialize(
      cache: Rails.cache,
      ranked_asset_ids: Rails.application.config.x.market_overview_ranked_asset_ids,
      ranking_basis: Rails.application.config.x.market_overview_ranking_basis,
      stale_ttl: Rails.application.config.x.market_overview_snapshot_stale_ttl,
      lock_ttl: Rails.application.config.x.market_overview_refresh_lock_ttl
    )
      @cache = cache
      @ranked_asset_ids = Array(ranked_asset_ids)
      @ranking_basis = ranking_basis
      @stale_ttl = stale_ttl
      @lock_ttl = lock_ttl
    end

    def read_snapshot
      @cache.read(snapshot_key)
    end

    def write_snapshot(payload, metadata: {})
      @cache.write(snapshot_key, payload, expires_in: @stale_ttl)
      @cache.write(
        metadata_key,
        metadata.merge(
          "generated_at" => payload[:generated_at] || payload["generated_at"],
          "ranking_basis" => @ranking_basis,
          "asset_ids" => @ranked_asset_ids
        ),
        expires_in: @stale_ttl
      )
      payload
    end

    def with_refresh_lock
      token = SecureRandom.uuid
      acquired = @cache.write(lock_key, token, expires_in: @lock_ttl, unless_exist: true)
      return false unless acquired

      begin
        yield
      ensure
        @cache.delete(lock_key) if @cache.read(lock_key) == token
      end
    end

    private

    def snapshot_key
      ["market-overview", "snapshot", "v3", @ranking_basis, @ranked_asset_ids.join("-")].join(":")
    end

    def metadata_key
      ["market-overview", "snapshot-meta", "v3", @ranking_basis, @ranked_asset_ids.join("-")].join(":")
    end

    def lock_key
      ["market-overview", "snapshot-lock", "v3", @ranking_basis, @ranked_asset_ids.join("-")].join(":")
    end
  end
end
