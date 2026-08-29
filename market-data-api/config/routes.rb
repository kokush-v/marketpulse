Rails.application.routes.draw do
  get "/up", to: proc { [200, { "Content-Type" => "application/json" }, ['{"status":"ok"}']] }

  namespace :api do
    namespace :v1 do
      get "market-overview", to: "market_overview#show"
      get "assets/search", to: "assets#search"
      get "news", to: "news#index"
      get "price-charts", to: "price_charts#show"
    end
  end
end
