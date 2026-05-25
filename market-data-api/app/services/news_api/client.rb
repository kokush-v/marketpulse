require "json"
require "net/http"
require "uri"

module NewsApi
  class Error < StandardError; end
  class ProviderError < Error; end
  class RateLimitError < Error; end

  class Client
    DEFAULT_BASE_URL = "https://newsapi.org/v2".freeze

    def initialize(base_url: DEFAULT_BASE_URL, api_key:)
      @base_url = base_url
      @api_key = api_key
    end

    def search(query:, page_size: 10)
      raise ProviderError, "NewsAPI key is not configured" if @api_key.to_s.strip == ""

      get_json(
        "/everything",
        {
          q: query,
          language: "en",
          sortBy: "publishedAt",
          pageSize: page_size,
          searchIn: "title,description"
        }
      )
    end

    private

    def get_json(path, query = {})
      uri = URI.join(@base_url.end_with?("/") ? @base_url : "#{@base_url}/", path.delete_prefix("/"))
      uri.query = URI.encode_www_form(query.compact.transform_values(&:to_s))

      request = Net::HTTP::Get.new(uri)
      request["Accept"] = "application/json"
      request["X-Api-Key"] = @api_key

      response = Net::HTTP.start(
        uri.host,
        uri.port,
        use_ssl: uri.scheme == "https",
        open_timeout: 10,
        read_timeout: 10
      ) do |http|
        http.request(request)
      end

      handle_response(response)
    rescue JSON::ParserError => error
      raise ProviderError, "NewsAPI returned malformed JSON: #{error.message}"
    rescue StandardError => error
      raise error if error.is_a?(Error)

      raise ProviderError, error.message.presence || "NewsAPI request failed"
    end

    def handle_response(response)
      body = response.body.to_s
      payload = body.strip.empty? ? {} : JSON.parse(body)

      case response.code.to_i
      when 200
        payload
      when 429
        raise RateLimitError, extract_message(payload, "NewsAPI rate limit reached")
      else
        raise ProviderError, extract_message(payload, "NewsAPI request failed with status #{response.code}")
      end
    end

    def extract_message(payload, fallback)
      return fallback unless payload.is_a?(Hash)

      %w[message error code status].each do |key|
        value = payload[key]
        return value if value.is_a?(String) && value.strip != ""
      end

      fallback
    end
  end
end
