require "json"
require "net/http"
require "time"
require "uri"

module CoinGecko
  class Error < StandardError; end
  class ProviderError < Error; end
  class RateLimitError < Error; end

  class Client
    DEFAULT_BASE_URL = "https://api.coingecko.com/api/v3".freeze

    def initialize(base_url: DEFAULT_BASE_URL, api_key: nil, open_timeout: 5, read_timeout: 5, max_retries: 1)
      @base_url = base_url
      @api_key = api_key
      @open_timeout = open_timeout
      @read_timeout = read_timeout
      @max_retries = max_retries
    end

    def coins_markets(ids:, vs_currency: "usd", sparkline: true, price_change_percentage: "24h")
      get_json(
        "/coins/markets",
        {
          ids: ids.join(","),
          vs_currency: vs_currency,
          order: "market_cap_desc",
          per_page: ids.length,
          page: 1,
          sparkline: sparkline,
          price_change_percentage: price_change_percentage
        }
      )
    end

    def coin_details(id)
      get_json(
        "/coins/#{id}",
        {
          localization: false,
          tickers: false,
          market_data: false,
          community_data: false,
          developer_data: false,
          sparkline: false
        }
      )
    end

    private

    def get_json(path, query = {})
      uri = URI.join(@base_url.end_with?("/") ? @base_url : "#{@base_url}/", path.delete_prefix("/"))
      uri.query = URI.encode_www_form(query.compact.transform_values(&:to_s))

      request = Net::HTTP::Get.new(uri)
      request["Accept"] = "application/json"
      request["x-cg-demo-api-key"] = @api_key if @api_key.to_s.strip != ""

      attempts = 0

      begin
        response = Net::HTTP.start(
          uri.host,
          uri.port,
          use_ssl: uri.scheme == "https",
          open_timeout: @open_timeout,
          read_timeout: @read_timeout
        ) do |http|
          http.request(request)
        end

        handle_response(response)
      rescue Net::OpenTimeout, Net::ReadTimeout, Errno::ECONNRESET, EOFError => error
        attempts += 1
        retry if attempts <= @max_retries

        raise ProviderError, error.message.presence || "CoinGecko request failed"
      end
    rescue JSON::ParserError => error
      raise ProviderError, "CoinGecko returned malformed JSON: #{error.message}"
    rescue StandardError => error
      raise error if error.is_a?(Error)

      raise ProviderError, error.message.presence || "CoinGecko request failed"
    end

    def handle_response(response)
      body = response.body.to_s
      payload = body.strip.empty? ? {} : JSON.parse(body)

      case response.code.to_i
      when 200
        payload
      when 429
        raise RateLimitError, extract_message(payload, "CoinGecko rate limit reached")
      else
        raise ProviderError, extract_message(payload, "CoinGecko request failed with status #{response.code}")
      end
    end

    def extract_message(payload, fallback)
      return fallback unless payload.is_a?(Hash)

      %w[error message status].each do |key|
        value = payload[key]
        return value if value.is_a?(String) && value.strip != ""
      end

      fallback
    end
  end
end
