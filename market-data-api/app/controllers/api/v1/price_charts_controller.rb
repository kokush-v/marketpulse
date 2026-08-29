require "time"

require Rails.root.join("app/services/coin_gecko/client")

module Api
  module V1
    class PriceChartsController < ApplicationController
      PERIOD_DAYS = { "24h" => 1, "7d" => 7, "30d" => 30, "1y" => 365 }.freeze
      MAX_ASSETS = 5

      rescue_from StandardError, with: :render_unexpected_error
      rescue_from CoinGecko::ProviderError, with: :render_provider_error
      rescue_from CoinGecko::RateLimitError, with: :render_rate_limited

      def show
        asset_ids = params[:asset_ids].to_s.split(",").map(&:strip).reject(&:blank?).uniq
        period = params[:period].to_s

        unless asset_ids.length.between?(1, MAX_ASSETS)
          return render_validation_error("Select between one and #{MAX_ASSETS} coins.")
        end
        return render_validation_error("Choose a supported chart period.") unless PERIOD_DAYS.key?(period)

        series = asset_ids.map do |asset_id|
          payload = Rails.application.config.x.market_data_client_factory.call.market_chart(
            id: asset_id,
            days: PERIOD_DAYS.fetch(period)
          )
          { asset_id: asset_id, points: normalize_points(payload) }
        end

        render json: { period: period, series: series }
      end

      private

      def normalize_points(payload)
        points = Array(payload["prices"]).filter_map do |point|
          next unless point.is_a?(Array) && point.length >= 2

          timestamp, price = point
          next unless timestamp.is_a?(Numeric) && price.is_a?(Numeric)

          { time: Time.at(timestamp / 1000.0).utc.iso8601, price: price.to_f }
        end
        raise CoinGecko::ProviderError, "CoinGecko returned no historical prices" if points.empty?

        points
      end

      def render_validation_error(detail)
        render json: { error: { code: "invalid_request", title: "Invalid chart request", detail: detail } }, status: :unprocessable_entity
      end

      def render_rate_limited(error)
        log_error(error, severity: :warn)
        render_provider_error_response(:too_many_requests, "Crypto market data is temporarily busy", "Please try again in a few moments.", "rate_limited")
      end

      def render_provider_error(error)
        log_error(error, severity: :error)
        render_provider_error_response(:bad_gateway, "Historical crypto data is temporarily unavailable", "Provider data is temporarily unavailable.", "provider_error")
      end

      def render_unexpected_error(error)
        log_error(error, severity: :error)
        render_provider_error_response(:internal_server_error, "Historical chart request failed", "An unexpected error occurred while loading chart data.", "internal_error")
      end

      def render_provider_error_response(status, title, detail, code)
        render json: { error: { code: code, title: title, detail: detail } }, status: status
      end

      def log_error(error, severity:)
        Rails.logger.public_send(severity, "[price-charts] #{error.class}: #{error.message}")
      end
    end
  end
end
