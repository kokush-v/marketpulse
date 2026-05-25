require Rails.root.join("app/services/news_api/client")

module Api
  module V1
    class NewsController < ApplicationController
      rescue_from StandardError, with: :render_unexpected_error
      rescue_from NewsApi::RateLimitError, with: :render_rate_limited
      rescue_from NewsApi::ProviderError, with: :render_provider_error

      def index
        query = params[:query].to_s.strip
        return render json: { articles: [] } if query == ""

        payload = Rails.application.config.x.news_api_client_factory.call.search(query: query)
        articles = Array(payload["articles"]).map do |article|
          {
            title: article["title"].to_s,
            summary: article["description"].to_s,
            url: article["url"].to_s,
            image_url: article["urlToImage"].presence,
            published_at: article["publishedAt"].presence,
            source: article.dig("source", "name").presence || "NewsAPI"
          }
        end

        render json: { articles: articles }
      end

      private

      def render_rate_limited(error)
        log_error(error, severity: :warn)
        render_error(
          status: :too_many_requests,
          code: "rate_limited",
          title: "Coin news is temporarily busy",
          detail: "Please try again in a few moments."
        )
      end

      def render_provider_error(error)
        log_error(error, severity: :error)
        render_error(
          status: :bad_gateway,
          code: "provider_error",
          title: "Coin news is temporarily unavailable",
          detail: "Provider news data is temporarily unavailable."
        )
      end

      def render_unexpected_error(error)
        log_error(error, severity: :error)
        render_error(
          status: :internal_server_error,
          code: "internal_error",
          title: "Coin news request failed",
          detail: "An unexpected error occurred while loading coin news."
        )
      end

      def log_error(error, severity:)
        Rails.logger.public_send(
          severity,
          "[coin-news] #{error.class}: #{error.message}\n#{Array(error.backtrace).first(10).join("\n")}"
        )
      end

      def render_error(status:, code:, title:, detail:)
        render json: {
          error: {
            code: code,
            title: title,
            detail: detail
          }
        }, status: status
      end
    end
  end
end
