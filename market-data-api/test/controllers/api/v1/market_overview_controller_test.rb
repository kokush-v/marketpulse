require "test_helper"

module Api
  module V1
    class MarketOverviewControllerTest < ActionDispatch::IntegrationTest
      setup do
        @original_factory = Rails.application.config.x.market_data_client_factory
        Rails.cache.clear
      end

      teardown do
        Rails.application.config.x.market_data_client_factory = @original_factory
        Rails.cache.clear
      end

      test "returns market overview payload" do
        Rails.application.config.x.market_data_client_factory = -> { StubClient.new }

        get "/api/v1/market-overview"

        assert_response :success
        body = JSON.parse(response.body)
        assert_equal "market-data-api", body["source"]
        assert_equal "Top 25 crypto assets by market capitalization", body["ranking_basis"]
        assert_equal 25, body["featured_assets"].length
        assert_equal 1, body["featured_assets"].first["related_news"].length
      end

      test "returns rate limit response when provider is throttled" do
        Rails.application.config.x.market_data_client_factory = -> { RateLimitedClient.new }

        get "/api/v1/market-overview"

        assert_response :too_many_requests
        body = JSON.parse(response.body)
        assert_equal "rate_limited", body.dig("error", "code")
      end

      test "returns a safe error response when the route crashes unexpectedly" do
        Rails.application.config.x.market_data_client_factory = lambda {
          raise StandardError, "unexpected crash for debugging"
        }

        get "/api/v1/market-overview"

        assert_response :internal_server_error
        body = JSON.parse(response.body)
        assert_equal "internal_error", body.dig("error", "code")
        assert_equal "An unexpected error occurred while loading market data.", body.dig("error", "detail")
      end

      test "returns service unavailable when refresh is already in progress and no snapshot is available" do
        Rails.application.config.x.market_data_client_factory = -> { RefreshInProgressClient.new }

        get "/api/v1/market-overview"

        assert_response :service_unavailable
        body = JSON.parse(response.body)
        assert_equal "refresh_in_progress", body.dig("error", "code")
      end

      test "reuses cached overview payload within the cache window" do
        snapshot = {
          "generated_at" => "2026-05-27T20:00:00Z",
          "source" => "cached-market-data-api",
          "ranking_basis" => "Top 25 crypto assets by market capitalization",
          "hero_asset_id" => "bitcoin",
          "featured_assets" => [],
          "hero_chart" => [],
          "top_gainers" => [],
          "top_losers" => []
        }

        MarketOverview::SnapshotStore.new.write_snapshot(snapshot, metadata: { "refresh_reason" => "test" })

        get "/api/v1/market-overview"
        assert_response :success

        get "/api/v1/market-overview"
        assert_response :success

        body = JSON.parse(response.body)
        assert_equal "cached-market-data-api", body["source"]
      end

      class StubClient
        def coins_markets(ids:, **)
          ids.map.with_index(1) do |id, index|
            {
              "id" => id,
              "symbol" => id[0, 3],
              "name" => id.tr("-", " ").split.map(&:capitalize).join(" "),
              "image" => "https://example.com/#{id}.png",
              "current_price" => 1000 + index,
              "market_cap" => 1_000_000_000 + index,
              "market_cap_rank" => index,
              "total_volume" => 500_000_000 + index,
              "high_24h" => 1010 + index,
              "low_24h" => 990 + index,
              "price_change_24h" => 10 + index,
              "price_change_percentage_24h" => 1.0 + index,
              "last_updated" => "2026-05-21T12:00:00.000Z",
              "sparkline_in_7d" => { "price" => [950 + index, 975 + index, 1000 + index] }
            }
          end
        end

        def coin_details(id)
          {
            "categories" => ["Layer 1"],
            "description" => { "en" => "#{id} description" },
            "links" => { "homepage" => ["https://example.com/#{id}"] },
            "status_updates" => [
              {
                "title" => "#{id.tr('-', ' ').split.map(&:capitalize).join(' ')} institutional update",
                "description" => "<p>Demand stayed resilient across the latest session.</p>",
                "article_url" => "https://example.com/#{id}/news",
                "created_at" => "2026-05-21T12:00:00.000Z",
                "project" => { "name" => "CoinGecko" }
              }
            ]
          }
        end
      end

      class RateLimitedClient < StubClient
        def coins_markets(ids:, **)
          super
          raise CoinGecko::RateLimitError, "CoinGecko rate limit reached"
        end
      end

      class RefreshInProgressClient < StubClient
        def coins_markets(ids:, **)
          super
          raise CoinGecko::RefreshInProgressError, "Market overview refresh is already in progress"
        end
      end
    end
  end
end
