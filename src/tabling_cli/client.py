from __future__ import annotations

from typing import Any

import httpx

from tabling_cli.config import TablingConfig


class TablingAPIError(Exception):
    """API 요청 실패 시 발생하는 예외."""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        if error_code:
            super().__init__(f"[{status_code}/{error_code}] {message}")
        else:
            super().__init__(f"[{status_code}] {message}")


class TablingClient:
    """Tabling mobile-v2-api.tabling.co.kr 클라이언트.

    공개 조회(검색, 식당 상세, 큐레이션)는 인증 불필요.
    waitlist 등록/취소는 모바일 앱 세션 필요 (미구현).
    """

    def __init__(self, config: TablingConfig | None = None) -> None:
        self.config = config or TablingConfig()
        self._client = httpx.AsyncClient(
            base_url=self.config.api_base_url,
            headers=self._build_headers(),
            timeout=30.0,
        )

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "app-platform": "WEB",
        }
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            resp = await self._client.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise TablingAPIError(
                status_code=0,
                message=f"요청 실패: {exc}",
            ) from exc

        payload: Any
        try:
            payload = resp.json()
        except Exception as exc:
            if resp.is_error:
                raise TablingAPIError(
                    status_code=resp.status_code,
                    message=resp.text,
                ) from exc
            raise TablingAPIError(
                status_code=resp.status_code,
                message=f"JSON 파싱 실패: {resp.text[:200]}",
            ) from exc

        if resp.is_error:
            message = resp.text
            error_code: str | None = None
            if isinstance(payload, dict):
                raw_error = payload.get("error")
                if isinstance(raw_error, dict):
                    message = (
                        raw_error.get("message")
                        or raw_error.get("name")
                        or message
                    )
                    error_code = raw_error.get("errorCode")
            raise TablingAPIError(
                status_code=resp.status_code,
                message=message,
                error_code=error_code,
            )

        if not isinstance(payload, dict):
            raise TablingAPIError(
                status_code=resp.status_code,
                message=f"예상하지 못한 응답 형식: {type(payload).__name__}",
            )

        if isinstance(payload.get("error"), dict):
            raw_error = payload["error"]
            raise TablingAPIError(
                status_code=int(raw_error.get("status") or resp.status_code),
                message=raw_error.get("message")
                or raw_error.get("name")
                or "알 수 없는 API 오류",
                error_code=raw_error.get("errorCode"),
            )

        return payload

    async def search(
        self,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """POST /v1/search/restaurants/map — 식당 검색."""
        body: dict[str, Any] = {"keyword": keyword or "", "page": page, "pageSize": page_size}
        return await self._request("POST", "/v1/search/restaurants/map", json=body)

    async def get_shop(self, shop_id: str) -> dict[str, Any]:
        """GET /v1/restaurant/{restaurantIdx} — 식당 상세."""
        return await self._request("GET", f"/v1/restaurant/{shop_id}")

    async def get_reviews(self, shop_id: str) -> dict[str, Any]:
        """GET /v1/review/restaurant/{restaurantIdx} — 리뷰 조회."""
        return await self._request("GET", f"/v1/review/restaurant/{shop_id}")

    async def get_curations(self, home: bool = True) -> dict[str, Any]:
        """GET /v1/curations — 큐레이션 목록."""
        return await self._request("GET", "/v1/curations", params={"isHome": home})

    async def get_curation_restaurants(self, curation_id: str) -> dict[str, Any]:
        """GET /v1/curation-restaurants/{curationId} — 큐레이션 식당 목록."""
        return await self._request("GET", f"/v1/curation-restaurants/{curation_id}")

    async def get_brands(self, page: int = 1, size: int = 10) -> dict[str, Any]:
        """GET /v1/brands/ — 브랜드 목록."""
        return await self._request(
            "GET", "/v1/brands/", params={"page": page, "pageSize": size}
        )

    async def register_waitlist(
        self,
        shop_id: str,
        party_size: int,
    ) -> dict[str, Any]:
        """대기열 등록 (모바일 앱 RE 필요 — placeholder)."""
        return await self._request(
            "POST",
            f"/v1/restaurant/{shop_id}/waitlist",
            json={"partySize": party_size},
        )

    async def cancel_waitlist(self, waitlist_id: str) -> dict[str, Any]:
        """대기열 취소 (모바일 앱 RE 필요 — placeholder)."""
        return await self._request("DELETE", f"/v1/waitlist/{waitlist_id}")

    async def get_waitlist_status(self, waitlist_id: str) -> dict[str, Any]:
        """대기 상태 조회 (모바일 앱 RE 필요 — placeholder)."""
        return await self._request("GET", f"/v1/waitlist/{waitlist_id}")

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> TablingClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
