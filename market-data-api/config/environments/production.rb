require "active_support/core_ext/integer/time"

Rails.application.configure do
  config.cache_classes = true
  config.eager_load = true
  config.consider_all_requests_local = false
  config.action_controller.perform_caching = true
  config.log_level = ENV.fetch("RAILS_LOG_LEVEL", "info")
  config.active_support.report_deprecations = false

  redis_url = ENV.fetch("REDIS_URL")
  config.cache_store = :redis_cache_store, {
    url: redis_url,
    connect_timeout: 5,
    read_timeout: 5,
    write_timeout: 5,
    reconnect_attempts: 1,
    error_handler: lambda do |method:, returning:, exception:|
      Rails.logger.error("[cache] #{method} failed: #{exception.class}: #{exception.message}; returning #{returning.inspect}")
    end
  }
end
