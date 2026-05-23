require Rails.root.join("app/services/coingecko/client")

module Api
  module V1
    class AssetsController < ApplicationController
      CACHE_TTL = 15.minutes

      rescue_from StandardError, with: :render_unexpected_error
      rescue_from CoinGecko::RateLimitError, with: :render_rate_limited
      rescue_from CoinGecko::ProviderError, with: :render_provider_error

      def search
        query = params[:q].to_s.strip.downcase
        return render json: { items: [] } if query == ""

        market_rows = Rails.cache.fetch(cache_key, expires_in: CACHE_TTL) do
          Rails.application.config.x.market_data_client_factory.call.coins_markets(
            ids: Array(Rails.application.config.x.market_overview_ranked_asset_ids),
            sparkline: false
          )
        end

        items = Array(market_rows)
          .select do |row|
            row["symbol"].to_s.downcase.include?(query) || row["name"].to_s.downcase.include?(query)
          end
          .sort_by { |row| row["market_cap_rank"] || Float::INFINITY }
          .first(8)
          .map do |row|
            {
              asset_id: row["id"],
              symbol: row["symbol"].to_s.upcase,
              name: row["name"].to_s,
              market_cap_rank: row["market_cap_rank"].to_i,
              current_price: row["current_price"].to_f,
              price_change_percentage_24h: row["price_change_percentage_24h"].to_f,
              image_url: row["image"].to_s
            }
          end

        render json: { items: items }
      end

      private

      def cache_key
        [
          "asset-search-universe",
          "v1",
          Array(Rails.application.config.x.market_overview_ranked_asset_ids).join("-")
        ].join(":")
      end

      def render_rate_limited(error)
        log_error(error, severity: :warn)
        render_error(
          status: :too_many_requests,
          code: "rate_limited",
          title: "Crypto market data is temporarily busy",
          detail: "Please try again in a few moments."
        )
      end

      def render_provider_error(error)
        log_error(error, severity: :error)
        render_error(
          status: :bad_gateway,
          code: "provider_error",
          title: "Crypto asset search is temporarily unavailable",
          detail: "Provider data is temporarily unavailable."
        )
      end

      def render_unexpected_error(error)
        log_error(error, severity: :error)
        render_error(
          status: :internal_server_error,
          code: "internal_error",
          title: "Asset search request failed",
          detail: "An unexpected error occurred while searching assets."
        )
      end

      def log_error(error, severity:)
        Rails.logger.public_send(
          severity,
          "[asset-search] #{error.class}: #{error.message}\n#{Array(error.backtrace).first(10).join("\n")}"
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
