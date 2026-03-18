from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class APIErrorDetail(APIModel):
    status: int | None = None
    name: str | None = None
    message: str | None = None
    errorCode: str | None = None


class APIErrorResponse(APIModel):
    error: APIErrorDetail


class Restaurant(APIModel):
    mongoId: str | None = Field(default=None, alias="_id")
    restaurantIdx: int | None = None
    restaurantName: str | None = None
    rating: float | None = None
    reviewCount: int | None = None
    summaryAddress: str | None = None
    useRemoteWaiting: bool | None = None
    waitingCount: int | None = None
    useReservation: bool | None = None
    latitude: float | None = None
    longitude: float | None = None
    recommendedMenus: list[Any] = Field(default_factory=list)
    restaurantOpenStatus: str | dict[str, Any] | None = None
    openStatus: str | None = None
    categories: str | list[str] | None = None
    classification: str | None = None
    thumbnail: str | None = None


class SearchResult(APIModel):
    items: list[Restaurant] = Field(default_factory=list, alias="list")
    total: int = 0
    last: bool | list[Any] | dict[str, Any] | None = None


class RestaurantDetail(APIModel):
    idx: int
    name: str
    excerpt: str | None = None
    description: str | None = None
    categories: str | list[str] | None = None
    address: str | None = None
    tel: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    waitingCount: int | None = None
    useWaiting: bool | None = None
    useRemoteWaiting: bool | None = None
    useReservation: bool | None = None
    rating: float | None = None
    reviewTotalCount: int | None = None
    favoriteCount: int | None = None
    remoteWaitingStatus: str | None = None
    remoteWaitingLabel: str | None = None
    reservationStatus: str | None = None
    reservationLabel: str | None = None
    restaurantStatus: str | None = None
    restaurantStatusLabel: str | None = None
    waitingScopeMessage: str | None = None
    reservationOption: dict[str, Any] | None = None


class Review(APIModel):
    mongoId: str | None = Field(default=None, alias="_id")
    idx: str | int | None = None
    mobileUserIdx: int | None = None
    nickname: str | None = None
    reviewDate: str | None = None
    contents: str | None = None
    rating: float | None = None
    images: list[Any] = Field(default_factory=list)
    menuOrders: list[Any] = Field(default_factory=list)
    likeCount: int | None = None
    isLiked: bool | None = None
    reply: Any = None
    isBlinded: bool | None = None


class ReviewResult(APIModel):
    reviewTotalCount: int | None = None
    rating: float | None = None
    ratings: dict[str, Any] | None = None
    imageReviewTotalCount: int | None = None
    reviews: list[Review] = Field(default_factory=list)


class Curation(APIModel):
    id: str = Field(alias="_id")
    title: str
    subTitle: str | None = None
    deepLink: str | None = None
    isOn: bool | None = None
    isHome: bool | None = None
    rank: int | None = None
    emoji: str | None = None
    restaurantIdxes: list[int] = Field(default_factory=list)


class CurationResult(APIModel):
    items: list[Curation] = Field(default_factory=list, alias="list")
    totalCount: int = 0


class Brand(APIModel):
    id: str = Field(alias="_id")
    name: str
    categories: str | list[str] | None = None
    excerpt: str | None = None
    logo: str | None = None
    images: list[str] = Field(default_factory=list)
    externalLink: list[str] = Field(default_factory=list)
    externalVideoLink: list[str] = Field(default_factory=list)
    priority: int | None = None
    isPopular: bool | None = None
    status: str | None = None


class BrandResult(APIModel):
    items: list[Brand] = Field(default_factory=list, alias="list")
    totalCount: int = 0


class WaitlistEntry(APIModel):
    id: str | None = None
    shop_id: str | None = None
    party_size: int | None = None
    rank: int | None = None
    estimated_wait: str | None = None
    status: str | None = None


class WaitlistStatus(APIModel):
    id: str | None = None
    shop_id: str | None = None
    shop_name: str | None = None
    party_size: int | None = None
    rank: int | None = None
    estimated_wait: str | None = None
    status: str | None = None
