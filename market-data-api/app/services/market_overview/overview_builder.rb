module MarketOverview
  class OverviewBuilder
    FEATURED_ASSET_COUNT = 25
    MOVERS_UNIVERSE_COUNT = 25
    MOVERS_COUNT = 4

    def initialize(client:, ranked_asset_ids:, ranking_basis:)
      @client = client
      @ranked_asset_ids = ranked_asset_ids
      @ranking_basis = ranking_basis
    end

    def call
      asset_ids = @ranked_asset_ids.first(MOVERS_UNIVERSE_COUNT)
      market_rows = @client.coins_markets(ids: asset_ids)
      sorted_rows = sort_by_rank(market_rows)
      detail_map = build_detail_map(sorted_rows.first(FEATURED_ASSET_COUNT))
      featured_assets = sorted_rows.first(FEATURED_ASSET_COUNT).map { |row| build_featured_asset(row, detail_map[row["id"]]) }
      movers = sorted_rows.map { |row| build_mover(row) }

      {
        generated_at: Time.now.utc.iso8601,
        source: "market-data-api",
        ranking_basis: @ranking_basis,
        hero_asset_id: featured_assets.first && featured_assets.first[:id],
        featured_assets: featured_assets,
        hero_chart: featured_assets.first && featured_assets.first[:chart],
        top_gainers: movers.sort_by { |asset| -(asset[:price_change_percentage_24h] || 0) }.first(MOVERS_COUNT),
        top_losers: movers.sort_by { |asset| asset[:price_change_percentage_24h] || 0 }.first(MOVERS_COUNT)
      }
    end

    private

    def sort_by_rank(rows)
      Array(rows).sort_by { |row| row["market_cap_rank"] || Float::INFINITY }
    end

    def build_detail_map(rows)
      rows.each_with_object({}) do |row, details|
        details[row["id"]] = @client.coin_details(row["id"])
      end
    end

    def build_featured_asset(row, details)
      {
        id: row["id"],
        symbol: row["symbol"].to_s.upcase,
        name: row["name"].to_s,
        market_cap_rank: row["market_cap_rank"].to_i,
        current_price: row["current_price"].to_f,
        price_change_24h: row["price_change_24h"].to_f,
        price_change_percentage_24h: row["price_change_percentage_24h"].to_f,
        market_cap: row["market_cap"].to_f,
        total_volume: row["total_volume"].to_f,
        high_24h: row["high_24h"].to_f,
        low_24h: row["low_24h"].to_f,
        image_url: row["image"].to_s,
        homepage: extract_homepage(details),
        description: extract_description(details),
        categories: Array(details&.dig("categories")).compact.first(3),
        chart: normalize_chart(row.dig("sparkline_in_7d", "price"), row["last_updated"]),
        related_news: extract_related_news(details)
      }
    end

    def build_mover(row)
      {
        id: row["id"],
        symbol: row["symbol"].to_s.upcase,
        name: row["name"].to_s,
        current_price: row["current_price"].to_f,
        price_change_24h: row["price_change_24h"].to_f,
        price_change_percentage_24h: row["price_change_percentage_24h"].to_f,
        market_cap_rank: row["market_cap_rank"].to_i,
        image_url: row["image"].to_s
      }
    end

    def normalize_chart(prices, last_updated)
      values = Array(prices).compact.map(&:to_f)
      return [] if values.empty?

      end_time = parse_time(last_updated)
      start_time = end_time - 7.days
      step_seconds = values.length > 1 ? ((7.days).to_f / (values.length - 1)) : 0

      values.each_with_index.map do |price, index|
        {
          time: (start_time + (step_seconds * index)).utc.iso8601,
          price: price,
          volume: 0.0
        }
      end
    end

    def parse_time(value)
      Time.parse(value.to_s).utc
    rescue ArgumentError, TypeError
      Time.now.utc
    end

    def extract_homepage(details)
      Array(details&.dig("links", "homepage")).find { |url| url.to_s.strip != "" }.to_s
    end

    def extract_description(details)
      description = details&.dig("description", "en").to_s.strip
      return "" if description == ""

      description.gsub(/<[^>]*>/, "").gsub(/\s+/, " ").strip
    end

    def extract_related_news(details)
      Array(details&.dig("status_updates")).filter_map do |item|
        title = item["title"].to_s.strip
        description = item["description"].to_s.gsub(/<[^>]*>/, "").gsub(/\s+/, " ").strip
        url = item["article_url"].to_s.strip
        source = item.dig("project", "name").to_s.strip
        published_at = item["created_at"].to_s.strip

        next if title == "" || description == "" || url == ""

        {
          title: title,
          summary: description,
          url: url,
          published_at: published_at,
          source: source == "" ? "CoinGecko" : source
        }
      end.first(3)
    end
  end
end
