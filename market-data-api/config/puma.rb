max_threads_count = ENV.fetch("RAILS_MAX_THREADS", Rails.application.config.x.market_data_puma_max_threads).to_i
min_threads_count = ENV.fetch("RAILS_MIN_THREADS", Rails.application.config.x.market_data_puma_min_threads).to_i

threads min_threads_count, max_threads_count

environment ENV.fetch("RAILS_ENV", "development")

workers ENV.fetch("WEB_CONCURRENCY", Rails.application.config.x.market_data_puma_workers).to_i if ENV.fetch("RAILS_ENV", "development") == "production"

preload_app!

plugin :tmp_restart
