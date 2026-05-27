require "test_helper"

module MarketOverview
  class SnapshotRefresherTest < ActiveSupport::TestCase
    test "writes a refreshed snapshot when the refresh succeeds" do
      snapshot_store = FakeSnapshotStore.new
      refresher = SnapshotRefresher.new(
        snapshot_store: snapshot_store,
        logger: Logger.new(nil),
        builder_factory: -> { FakeBuilder.new({ "generated_at" => "2026-05-27T20:00:00Z", "source" => "market-data-api" }) }
      )

      payload = refresher.refresh!(reason: "scheduled_task")

      assert_equal "market-data-api", payload["source"]
      assert_equal "scheduled_task", snapshot_store.last_metadata["refresh_reason"]
      assert_equal "2026-05-27T20:00:00Z", snapshot_store.snapshot["generated_at"]
    end

    test "preserves the last successful snapshot when refresh fails" do
      cached_snapshot = { "generated_at" => "2026-05-27T19:00:00Z", "source" => "cached" }
      snapshot_store = FakeSnapshotStore.new(snapshot: cached_snapshot)
      refresher = SnapshotRefresher.new(
        snapshot_store: snapshot_store,
        logger: Logger.new(nil),
        builder_factory: -> { FailingBuilder.new }
      )

      payload = refresher.refresh!(reason: "scheduled_task")

      assert_equal "cached", payload["source"]
      assert_equal cached_snapshot, snapshot_store.snapshot
    end

    test "raises when no snapshot exists and cold start refresh fails" do
      snapshot_store = FakeSnapshotStore.new
      refresher = SnapshotRefresher.new(
        snapshot_store: snapshot_store,
        logger: Logger.new(nil),
        builder_factory: -> { FailingBuilder.new }
      )

      assert_raises(CoinGecko::ProviderError) do
        refresher.refresh!(reason: "cold_start")
      end
    end

    test "returns a waited snapshot when another refresh is already in progress" do
      waited_snapshot = { "generated_at" => "2026-05-27T19:30:00Z", "source" => "waited" }
      snapshot_store = FakeSnapshotStore.new(lock_result: false, waited_snapshot: waited_snapshot)
      refresher = SnapshotRefresher.new(
        snapshot_store: snapshot_store,
        logger: Logger.new(nil),
        builder_factory: -> { FailingBuilder.new }
      )

      payload = refresher.refresh!(reason: "cold_start")

      assert_equal "waited", payload["source"]
      assert_equal SnapshotRefresher::REFRESH_WAIT_TIMEOUT_SECONDS, snapshot_store.wait_args[:timeout_seconds]
    end

    test "raises refresh in progress when another refresh is already in progress and no snapshot appears" do
      snapshot_store = FakeSnapshotStore.new(lock_result: false)
      refresher = SnapshotRefresher.new(
        snapshot_store: snapshot_store,
        logger: Logger.new(nil),
        builder_factory: -> { FailingBuilder.new }
      )

      assert_raises(CoinGecko::RefreshInProgressError) do
        refresher.refresh!(reason: "cold_start")
      end
    end

    class FakeSnapshotStore
      attr_reader :snapshot, :last_metadata, :wait_args

      def initialize(snapshot: nil, lock_result: nil, waited_snapshot: nil)
        @snapshot = snapshot
        @lock_result = lock_result
        @waited_snapshot = waited_snapshot
      end

      def read_snapshot
        @snapshot
      end

      def write_snapshot(payload, metadata: {})
        @snapshot = payload
        @last_metadata = metadata
        payload
      end

      def with_refresh_lock
        return @lock_result unless @lock_result.nil?

        yield
      end

      def wait_for_snapshot(timeout_seconds:, poll_interval_seconds:)
        @wait_args = {
          timeout_seconds: timeout_seconds,
          poll_interval_seconds: poll_interval_seconds
        }
        @waited_snapshot
      end
    end

    class FakeBuilder
      def initialize(payload)
        @payload = payload
      end

      def call
        @payload
      end
    end

    class FailingBuilder
      def call
        raise CoinGecko::ProviderError, "upstream unavailable"
      end
    end
  end
end
