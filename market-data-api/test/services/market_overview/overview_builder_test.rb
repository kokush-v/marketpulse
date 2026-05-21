require "test_helper"

module MarketOverview
  class OverviewBuilderTest < ActiveSupport::TestCase
    test "builds featured assets and movers payload" do
      client = FakeCoinGeckoClient.new

      payload = OverviewBuilder.new(
        client: client,
        ranked_asset_ids: %w[bitcoin ethereum tether ripple binancecoin solana usd-coin dogecoin tron cardano],
        ranking_basis: "Top 10 crypto assets by market capitalization"
      ).call

      assert_equal "market-data-api", payload[:source]
      assert_equal "Top 10 crypto assets by market capitalization", payload[:ranking_basis]
      assert_equal "bitcoin", payload[:hero_asset_id]
      assert_equal 5, payload[:featured_assets].size
      assert_equal 4, payload[:top_gainers].size
      assert_equal 4, payload[:top_losers].size
      assert_equal 3, payload[:hero_chart].size
      assert_equal %w[bitcoin ethereum tether ripple binancecoin solana usd-coin dogecoin tron cardano], client.coins_markets_calls.first
      assert_equal %w[bitcoin ethereum tether ripple binancecoin], client.coin_details_calls
    end

    class FakeCoinGeckoClient
      attr_reader :coins_markets_calls, :coin_details_calls

      def initialize
        @coins_markets_calls = []
        @coin_details_calls = []
      end

      def coins_markets(ids:, **)
        @coins_markets_calls << ids

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
            "price_change_24h" => (index.even? ? -1 : 1) * (10 + index),
            "price_change_percentage_24h" => (index.even? ? -1 : 1) * (1.0 + index),
            "last_updated" => "2026-05-21T12:00:00.000Z",
            "sparkline_in_7d" => { "price" => [950 + index, 975 + index, 1000 + index] }
          }
        end
      end

      def coin_details(id)
        @coin_details_calls << id
        {
          "categories" => ["Layer 1", "Payments"],
          "description" => { "en" => "<p>#{id} description</p>" },
          "links" => { "homepage" => ["https://example.com/#{id}"] }
        }
      end
    end
  end
end
