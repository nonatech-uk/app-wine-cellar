"""Pydantic request/response models."""

from datetime import datetime

from pydantic import BaseModel


class UserInfo(BaseModel):
    email: str
    display_name: str
    role: str


class WineItem(BaseModel):
    id: int
    producer: str
    name: str
    vintage: int | None
    region: str | None
    country: str | None
    wine_type: str | None
    style: str | None
    grape_variety: str | None
    abv: float | None
    vivino_avg_rating: float | None
    avg_personal_rating: float | None = None
    last_tasted: str | None = None
    tasting_count: int = 0


class WineDetail(WineItem):
    vivino_url: str | None
    vivino_ratings_count: int | None
    drinking_window: str | None
    created_at: str
    updated_at: str
    cellar_quantity: int = 0
    cellar_location: str | None = None
    is_wishlisted: bool = False


class WineList(BaseModel):
    items: list[WineItem]
    total: int
    has_more: bool


class WineUpdate(BaseModel):
    producer: str | None = None
    name: str | None = None
    vintage: int | None = None
    region: str | None = None
    country: str | None = None
    wine_type: str | None = None
    style: str | None = None
    grape_variety: str | None = None
    abv: float | None = None
    drinking_window: str | None = None


class LogEntry(BaseModel):
    id: int
    wine_id: int
    logged_at: str
    source: str
    rating: float | None
    review: str | None
    personal_note: str | None
    location: str | None
    gps_lat: float | None
    gps_lng: float | None
    label_image_filename: str | None
    pipeline_item_id: str | None
    # joined wine fields for recent log
    wine_producer: str | None = None
    wine_name: str | None = None
    wine_vintage: int | None = None


class LogCreate(BaseModel):
    rating: float | None = None
    review: str | None = None
    personal_note: str | None = None
    location: str | None = None


class LogUpdate(BaseModel):
    rating: float | None = None
    review: str | None = None
    personal_note: str | None = None
    location: str | None = None


class CellarItem(BaseModel):
    id: int
    wine_id: int
    quantity: int
    storage_location: str | None
    purchase_date: str | None
    purchase_price: float | None
    purchase_currency: str | None
    notes: str | None
    updated_at: str
    wine_producer: str | None = None
    wine_name: str | None = None
    wine_vintage: int | None = None
    wine_type: str | None = None


class CellarCreate(BaseModel):
    wine_id: int
    quantity: int = 1
    storage_location: str | None = None
    purchase_date: str | None = None
    purchase_price: float | None = None
    purchase_currency: str = "GBP"
    notes: str | None = None


class CellarUpdate(BaseModel):
    quantity: int | None = None
    storage_location: str | None = None
    purchase_date: str | None = None
    purchase_price: float | None = None
    notes: str | None = None


class WishlistItem(BaseModel):
    id: int
    wine_id: int
    wishlisted_at: str
    notes: str | None
    acquired: bool
    wine_producer: str | None = None
    wine_name: str | None = None
    wine_vintage: int | None = None
    wine_type: str | None = None


class WishlistCreate(BaseModel):
    wine_id: int
    notes: str | None = None


class WishlistUpdate(BaseModel):
    notes: str | None = None
    acquired: bool | None = None


class OverviewStats(BaseModel):
    total_wines: int
    total_countries: int
    total_tastings: int
    avg_rating: float | None
    cellar_bottles: int
    tastings_this_month: int


class CountryStat(BaseModel):
    country: str
    count: int
    avg_rating: float | None


class TimelinePoint(BaseModel):
    month: str
    count: int


class IngestResult(BaseModel):
    wine_id: int
    log_id: int
