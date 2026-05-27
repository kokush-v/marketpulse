require_relative "boot"

require "rails"
require "action_controller/railtie"
require "etc"

Bundler.require(*Rails.groups)

MARKET_OVERVIEW_TOP_25_CRYPTO_ASSET_IDS = %w[
  bitcoin ethereum tether ripple binancecoin solana usd-coin dogecoin tron cardano
  wrapped-bitcoin chainlink avalanche-2 stellar sui shiba-inu hedera bitcoin-cash
  litecoin toncoin polkadot uniswap leo-token monero pepe
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

    config.x.coingecko_api_key = ENV["COINGECKO_API_KEY"]
    config.x.coingecko_api_base_url = ENV.fetch("COINGECKO_API_BASE_URL", "https://api.coingecko.com/api/v3")
    config.x.coingecko_open_timeout_seconds = ENV.fetch("COINGECKO_OPEN_TIMEOUT_SECONDS", 5).to_i
    config.x.coingecko_read_timeout_seconds = ENV.fetch("COINGECKO_READ_TIMEOUT_SECONDS", 5).to_i
    config.x.coingecko_max_retries = ENV.fetch("COINGECKO_MAX_RETRIES", 1).to_i
    config.x.news_api_key = ENV["NEWS_API_KEY"]
    config.x.news_api_base_url = ENV.fetch("NEWS_API_BASE_URL", "https://newsapi.org/v2")
    config.x.market_overview_ranked_asset_ids = MARKET_OVERVIEW_TOP_25_CRYPTO_ASSET_IDS
    config.x.market_overview_ranking_basis = "Top 25 crypto assets by market capitalization"
    config.x.market_overview_detail_threads = ENV.fetch("MARKET_OVERVIEW_DETAIL_THREADS", 4).to_i
    config.x.market_overview_snapshot_fresh_ttl = ENV.fetch("MARKET_OVERVIEW_SNAPSHOT_FRESH_TTL_SECONDS", 3600).to_i
    config.x.market_overview_snapshot_stale_ttl = ENV.fetch("MARKET_OVERVIEW_SNAPSHOT_STALE_TTL_SECONDS", 21600).to_i
    config.x.market_overview_refresh_lock_ttl = ENV.fetch("MARKET_OVERVIEW_REFRESH_LOCK_TTL_SECONDS", 300).to_i
    config.x.market_overview_refresh_task_name = "market_overview:refresh"
    config.x.market_overview_scheduler_description = "Run `bundle exec rake market_overview:refresh` at or under the snapshot freshness interval in production."
    config.x.market_data_puma_workers = ENV.fetch("WEB_CONCURRENCY", [2, Etc.nprocessors].max).to_i
    config.x.market_data_puma_min_threads = ENV.fetch("RAILS_MIN_THREADS", 3).to_i
    config.x.market_data_puma_max_threads = ENV.fetch("RAILS_MAX_THREADS", 8).to_i
    config.x.market_data_client_factory = lambda do
      CoinGecko::Client.new(
        base_url: config.x.coingecko_api_base_url,
        api_key: config.x.coingecko_api_key,
        open_timeout: config.x.coingecko_open_timeout_seconds,
        read_timeout: config.x.coingecko_read_timeout_seconds,
        max_retries: config.x.coingecko_max_retries
      )
    end
    config.x.news_api_client_factory = lambda do
      NewsApi::Client.new(
        base_url: config.x.news_api_base_url,
        api_key: config.x.news_api_key
      )
    end
  end
end
