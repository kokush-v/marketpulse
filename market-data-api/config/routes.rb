Rails.application.routes.draw do
  get "/up", to: proc { [200, { "Content-Type" => "application/json" }, ['{"status":"ok"}']] }

  namespace :api do
    namespace :v1 do
      get "market-overview", to: "market_overview#show"
    end
  end
end
