require_relative "boot"

require "rails"
require "action_controller/railtie"

Bundler.require(*Rails.groups)

MARKET_OVERVIEW_TOP_10_CRYPTO_ASSET_IDS = %w[
  bitcoin ethereum tether ripple binancecoin solana usd-coin dogecoin tron cardano
].freeze

module MarketDataApi
  class Application < Rails::Application
    config.load_defaults 6.1
    config.api_only = true
    config.autoload_paths << Rails.root.join("app/services")
    config.eager_load_paths << Rails.root.join("app/services")

    config.generators do |generator|
      generator.helper false
      generator.assets false
      generator.test_framework :test_unit, fixture: false
    end

    config.cache_store = :memory_store

    config.x.coingecko_api_key = ENV["COINGECKO_API_KEY"]
    config.x.coingecko_api_base_url = ENV.fetch("COINGECKO_API_BASE_URL", "https://api.coingecko.com/api/v3")
    config.x.market_overview_ranked_asset_ids = MARKET_OVERVIEW_TOP_10_CRYPTO_ASSET_IDS
    config.x.market_overview_ranking_basis = "Top 10 crypto assets by market capitalization"
    config.x.market_data_client_factory = lambda do
      CoinGecko::Client.new(
        base_url: config.x.coingecko_api_base_url,
        api_key: config.x.coingecko_api_key
      )
    end
  end
end
