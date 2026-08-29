require "active_support/core_ext/integer/time"

Rails.application.configure do
  config.enable_reloading = true
  config.eager_load = false
  config.consider_all_requests_local = true
  config.action_controller.perform_caching = false
  config.active_support.deprecation = :log
  config.cache_store = :memory_store
  config.hosts << "host.docker.internal"
  config.hosts << "market-data-api"
end
