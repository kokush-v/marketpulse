require Rails.root.join("app/services/coingecko/client")
require Rails.root.join("app/services/market_overview/overview_builder")

module Api
  module V1
    class MarketOverviewController < ApplicationController
      CACHE_TTL = 1.hour

      rescue_from StandardError, with: :render_unexpected_error
      rescue_from CoinGecko::RateLimitError, with: :render_rate_limited
      rescue_from CoinGecko::ProviderError, with: :render_provider_error

      def show
        payload = Rails.cache.fetch(cache_key, expires_in: CACHE_TTL) do
          MarketOverview::OverviewBuilder.new(
            client: Rails.application.config.x.market_data_client_factory.call,
            ranked_asset_ids: Rails.application.config.x.market_overview_ranked_asset_ids,
            ranking_basis: Rails.application.config.x.market_overview_ranking_basis
          ).call
        end

        render json: payload
      end

      private

      def cache_key
        [
          "market-overview",
          "v2",
          Rails.application.config.x.market_overview_ranking_basis,
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
          title: "Crypto market data is temporarily unavailable",
          detail: "Provider data is temporarily unavailable."
        )
      end

      def render_unexpected_error(error)
        log_error(error, severity: :error)
        render_error(
          status: :internal_server_error,
          code: "internal_error",
          title: "Market overview request failed",
          detail: "An unexpected error occurred while loading market data."
        )
      end

      def log_error(error, severity:)
        Rails.logger.public_send(
          severity,
          "[market-overview] #{error.class}: #{error.message}\n#{Array(error.backtrace).first(10).join("\n")}"
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
