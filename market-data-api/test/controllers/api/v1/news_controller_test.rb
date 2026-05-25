require "test_helper"

module Api
  module V1
    class NewsControllerTest < ActionDispatch::IntegrationTest
      setup do
        @original_factory = Rails.application.config.x.news_api_client_factory
      end

      teardown do
        Rails.application.config.x.news_api_client_factory = @original_factory
      end

      test "returns normalized coin news articles" do
        Rails.application.config.x.news_api_client_factory = -> { StubClient.new }

        get "/api/v1/news", params: { query: "bitcoin" }

        assert_response :success
        body = JSON.parse(response.body)
        assert_equal 1, body["articles"].length
        assert_equal "Bitcoin reclaims momentum", body["articles"].first["title"]
        assert_equal "NewsAPI", body["articles"].first["source"]
        assert_equal "https://example.com/news/bitcoin.png", body["articles"].first["image_url"]
      end

      test "returns empty articles for blank query" do
        get "/api/v1/news", params: { query: "" }

        assert_response :success
        body = JSON.parse(response.body)
        assert_equal [], body["articles"]
      end

      test "maps upstream rate limit failures" do
        Rails.application.config.x.news_api_client_factory = -> { RateLimitedClient.new }

        get "/api/v1/news", params: { query: "bitcoin" }

        assert_response :too_many_requests
        body = JSON.parse(response.body)
        assert_equal "Please try again in a few moments.", body.dig("error", "detail")
      end

      class StubClient
        def search(query:, **)
          {
            "articles" => [
              {
                "title" => "Bitcoin reclaims momentum",
                "description" => "Spot demand improved during the US session.",
                "url" => "https://example.com/news/bitcoin",
                "urlToImage" => "https://example.com/news/bitcoin.png",
                "publishedAt" => "2026-05-25T09:30:00Z",
                "source" => { "name" => "NewsAPI" }
              }
            ]
          }
        end
      end

      class RateLimitedClient
        def search(query:, **)
          raise NewsApi::RateLimitError, "NewsAPI rate limit reached"
        end
      end
    end
  end
end
