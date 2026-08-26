max_threads_count = ENV.fetch("RAILS_MAX_THREADS", 8).to_i
min_threads_count = ENV.fetch("RAILS_MIN_THREADS", 3).to_i
environment_name = ENV.fetch("RAILS_ENV", "development")
bind_address = ENV.fetch("BIND", "tcp://0.0.0.0:#{ENV.fetch('PORT', 3001)}")

threads min_threads_count, max_threads_count

environment environment_name
bind bind_address

workers ENV.fetch("WEB_CONCURRENCY", 2).to_i if environment_name == "production"

preload_app!

plugin :tmp_restart
