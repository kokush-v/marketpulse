require "test_helper"

module Api
  module V1
    class PriceChartsControllerTest < ActionDispatch::IntegrationTest
      setup do
        @original_factory = Rails.application.config.x.market_data_client_factory
      end

      teardown do
        Rails.application.config.x.market_data_client_factory = @original_factory
      end

      test "returns normalized historical prices for up to five requested assets" do
        Rails.application.config.x.market_data_client_factory = -> { StubClient.new }

        get "/api/v1/price-charts", params: { asset_ids: "bitcoin,ethereum", period: "7d" }

        assert_response :success
        body = JSON.parse(response.body)
        assert_equal "7d", body["period"]
        assert_equal %w[bitcoin ethereum], body["series"].map { |series| series["asset_id"] }
        assert_equal "2026-08-29T00:00:00Z", body["series"].first["points"].first["time"]
      end

      test "rejects unsupported period and more than five assets" do
        get "/api/v1/price-charts", params: { asset_ids: "a,b,c,d,e,f", period: "2d" }

        assert_response :unprocessable_entity
        assert_equal "invalid_request", JSON.parse(response.body).dig("error", "code")
      end

      test "returns a safe response when the provider is throttled" do
        Rails.application.config.x.market_data_client_factory = -> { RateLimitedClient.new }

        get "/api/v1/price-charts", params: { asset_ids: "bitcoin", period: "24h" }

        assert_response :too_many_requests
        assert_equal "rate_limited", JSON.parse(response.body).dig("error", "code")
      end

      class StubClient
        def market_chart(id:, days:)
          raise "unexpected period" unless days == 7

          { "prices" => [[Time.utc(2026, 8, 29).to_i * 1000, id == "bitcoin" ? 100_000 : 3_500]] }
        end
      end

      class RateLimitedClient < StubClient
        def market_chart(**)
          raise ::CoinGecko::RateLimitError, "CoinGecko rate limit reached"
        end
      end
    end
  end
end
