export interface UserInfo {
  email: string
  display_name: string
  role: string
}

export interface WineItem {
  id: number
  producer: string
  name: string
  vintage: number | null
  region: string | null
  country: string | null
  wine_type: string | null
  style: string | null
  grape_variety: string | null
  abv: number | null
  vivino_avg_rating: number | null
  avg_personal_rating: number | null
  last_tasted: string | null
  tasting_count: number
}

export interface WineDetail extends WineItem {
  vivino_url: string | null
  vivino_ratings_count: number | null
  drinking_window: string | null
  created_at: string
  updated_at: string
  cellar_quantity: number
  cellar_location: string | null
  is_wishlisted: boolean
}

export interface WineList {
  items: WineItem[]
  total: number
  has_more: boolean
}

export interface LogEntry {
  id: number
  wine_id: number
  logged_at: string
  source: string
  rating: number | null
  review: string | null
  personal_note: string | null
  location: string | null
  gps_lat: number | null
  gps_lng: number | null
  label_image_filename: string | null
  pipeline_item_id: string | null
  wine_producer: string | null
  wine_name: string | null
  wine_vintage: number | null
}

export interface CellarItem {
  id: number
  wine_id: number
  quantity: number
  storage_location: string | null
  purchase_date: string | null
  purchase_price: number | null
  purchase_currency: string | null
  notes: string | null
  updated_at: string
  wine_producer: string | null
  wine_name: string | null
  wine_vintage: number | null
  wine_type: string | null
}

export interface WishlistItem {
  id: number
  wine_id: number
  wishlisted_at: string
  notes: string | null
  acquired: boolean
  wine_producer: string | null
  wine_name: string | null
  wine_vintage: number | null
  wine_type: string | null
}

export interface OverviewStats {
  total_wines: number
  total_countries: number
  total_tastings: number
  avg_rating: number | null
  cellar_bottles: number
  tastings_this_month: number
}

export interface CountryStat {
  country: string
  count: number
  avg_rating: number | null
}

export interface TimelinePoint {
  month: string
  count: number
}
