require "test_helper"

module MarketOverview
  class SnapshotFetcherTest < ActiveSupport::TestCase
    test "returns a reusable snapshot when one is already cached" do
      snapshot_store = FakeSnapshotStore.new(snapshot: { "source" => "cached" }, fresh: true)
      refresher = FakeSnapshotRefresher.new(snapshot: { "source" => "fresh" })

      payload = SnapshotFetcher.new(
        snapshot_store: snapshot_store,
        snapshot_refresher: refresher,
        logger: Logger.new(nil)
      ).fetch!

      assert_equal "cached", payload["source"]
      assert_equal 0, refresher.calls
    end

    test "refreshes when the cached snapshot is stale" do
      snapshot_store = FakeSnapshotStore.new(snapshot: { "source" => "stale" }, fresh: false)
      refresher = FakeSnapshotRefresher.new(snapshot: { "source" => "fresh" })

      payload = SnapshotFetcher.new(
        snapshot_store: snapshot_store,
        snapshot_refresher: refresher,
        logger: Logger.new(nil)
      ).fetch!

      assert_equal "fresh", payload["source"]
      assert_equal 1, refresher.calls
      assert_equal ["stale_snapshot"], refresher.reasons
    end

    test "refreshes on cold start when no cached snapshot exists" do
      snapshot_store = FakeSnapshotStore.new(snapshot: nil)
      refresher = FakeSnapshotRefresher.new(snapshot: { "source" => "fresh" })

      payload = SnapshotFetcher.new(
        snapshot_store: snapshot_store,
        snapshot_refresher: refresher,
        logger: Logger.new(nil)
      ).fetch!

      assert_equal "fresh", payload["source"]
      assert_equal 1, refresher.calls
      assert_equal ["cold_start"], refresher.reasons
    end

    class FakeSnapshotStore
      def initialize(snapshot:, fresh: false)
        @snapshot = snapshot
        @fresh = fresh
      end

      def read_snapshot
        @snapshot
      end

      def read_metadata
        @snapshot ? { "generated_at" => "2026-05-27T20:00:00Z" } : nil
      end

      def snapshot_fresh?(_metadata = nil, now: Time.now.utc)
        @fresh
      end
    end

    class FakeSnapshotRefresher
      attr_reader :calls, :reasons

      def initialize(snapshot:)
        @snapshot = snapshot
        @calls = 0
        @reasons = []
      end

      def refresh!(reason:)
        @calls += 1
        @reasons << reason
        @snapshot
      end
    end
  end
end
