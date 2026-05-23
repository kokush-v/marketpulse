require "test_helper"

module Api
  module V1
    class AssetsControllerTest < ActionDispatch::IntegrationTest
      setup do
        @original_factory = Rails.application.config.x.market_data_client_factory
        Rails.cache.clear
      end

      teardown do
        Rails.application.config.x.market_data_client_factory = @original_factory
        Rails.cache.clear
      end

      test "returns matched assets from the ranked universe" do
        Rails.application.config.x.market_data_client_factory = -> { StubClient.new }

        get "/api/v1/assets/search", params: { q: "bit" }

        assert_response :success
        body = JSON.parse(response.body)
        assert_equal "bitcoin", body["items"].first["asset_id"]
      end

      test "returns empty items for blank query" do
        get "/api/v1/assets/search", params: { q: "" }

        assert_response :success
        body = JSON.parse(response.body)
        assert_equal [], body["items"]
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
              "market_cap_rank" => index,
              "price_change_percentage_24h" => 1.0 + index
            }
          end
        end
      end
    end
  end
end
