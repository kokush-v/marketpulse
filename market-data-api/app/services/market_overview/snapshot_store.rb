require "securerandom"
require "time"

module MarketOverview
  class SnapshotStore
    def initialize(
      cache: Rails.cache,
      ranked_asset_ids: Rails.application.config.x.market_overview_ranked_asset_ids,
      ranking_basis: Rails.application.config.x.market_overview_ranking_basis,
      fresh_ttl: Rails.application.config.x.market_overview_snapshot_fresh_ttl,
      stale_ttl: Rails.application.config.x.market_overview_snapshot_stale_ttl,
      lock_ttl: Rails.application.config.x.market_overview_refresh_lock_ttl
    )
      @cache = cache
      @ranked_asset_ids = Array(ranked_asset_ids)
      @ranking_basis = ranking_basis
      @fresh_ttl = fresh_ttl
      @stale_ttl = stale_ttl
      @lock_ttl = lock_ttl
    end

    def read_snapshot
      @cache.read(snapshot_key)
    end

    def read_metadata
      @cache.read(metadata_key)
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

    def snapshot_fresh?(metadata = read_metadata, now: Time.now.utc)
      generated_at = parse_time(metadata && metadata["generated_at"])
      return false if generated_at.nil?

      (now - generated_at) <= @fresh_ttl
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

    def lock_held?
      !@cache.read(lock_key).nil?
    end

    def wait_for_snapshot(timeout_seconds:, poll_interval_seconds:)
      deadline = Process.clock_gettime(Process::CLOCK_MONOTONIC) + timeout_seconds

      loop do
        snapshot = read_snapshot
        return snapshot if snapshot
        return nil if Process.clock_gettime(Process::CLOCK_MONOTONIC) >= deadline
        return nil unless lock_held?

        sleep poll_interval_seconds
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

    def parse_time(value)
      return nil if value.to_s.strip == ""

      Time.parse(value.to_s).utc
    rescue ArgumentError, TypeError
      nil
    end
  end
end
