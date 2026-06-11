require "test_helper"

module MarketOverview
  class SnapshotStoreTest < ActiveSupport::TestCase
    include ActiveSupport::Testing::TimeHelpers

    test "treats a snapshot as fresh for up to fifteen minutes" do
      cache = ActiveSupport::Cache::MemoryStore.new
      store = SnapshotStore.new(
        cache: cache,
        fresh_ttl: 15.minutes,
        stale_ttl: 30.minutes,
        lock_ttl: 5.minutes
      )

      store.write_snapshot(
        { "generated_at" => "2026-05-27T20:00:00Z", "source" => "cached" },
        metadata: { "refresh_reason" => "test" }
      )

      assert store.snapshot_fresh?(store.read_metadata, now: Time.parse("2026-05-27T20:15:00Z"))
      assert_not store.snapshot_fresh?(store.read_metadata, now: Time.parse("2026-05-27T20:15:01Z"))
    end

    test "expires snapshot payload and metadata after thirty minutes" do
      cache = ActiveSupport::Cache::MemoryStore.new
      store = SnapshotStore.new(
        cache: cache,
        fresh_ttl: 15.minutes,
        stale_ttl: 30.minutes,
        lock_ttl: 5.minutes
      )

      travel_to Time.utc(2026, 5, 27, 20, 0, 0) do
        store.write_snapshot(
          { "generated_at" => "2026-05-27T20:00:00Z", "source" => "cached" },
          metadata: { "refresh_reason" => "test" }
        )
      end

      travel_to Time.utc(2026, 5, 27, 20, 29, 59) do
        assert_equal "cached", store.read_snapshot["source"]
        assert_equal "test", store.read_metadata["refresh_reason"]
      end

      travel_to Time.utc(2026, 5, 27, 20, 30, 1) do
        assert_nil store.read_snapshot
        assert_nil store.read_metadata
      end
    end
  end
end
