"""Dataclasses for Google Search Console API responses.

Each model exposes a ``from_api`` classmethod that maps the camelCase fields
returned by the Google APIs onto snake_case attributes, using ``.get(...)``
defaults so partial payloads never raise.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Site:
    """A verified property in Search Console (``webmasters.sites``)."""

    site_url: str
    permission_level: str = ""

    @classmethod
    def from_api(cls, data: dict) -> Site:
        return cls(
            site_url=data.get("siteUrl", ""),
            permission_level=data.get("permissionLevel", ""),
        )


@dataclass
class SearchAnalyticsRow:
    """A single row of a search-analytics query result."""

    keys: list[str] = field(default_factory=list)
    clicks: float = 0.0
    impressions: float = 0.0
    ctr: float = 0.0
    position: float = 0.0

    @classmethod
    def from_api(cls, data: dict) -> SearchAnalyticsRow:
        return cls(
            keys=list(data.get("keys", [])),
            clicks=data.get("clicks", 0.0),
            impressions=data.get("impressions", 0.0),
            ctr=data.get("ctr", 0.0),
            position=data.get("position", 0.0),
        )


@dataclass
class SearchAnalyticsResponse:
    """The envelope returned by ``searchanalytics.query``."""

    rows: list[SearchAnalyticsRow] = field(default_factory=list)
    response_aggregation_type: str = ""

    @classmethod
    def from_api(cls, data: dict) -> SearchAnalyticsResponse:
        return cls(
            rows=[SearchAnalyticsRow.from_api(r) for r in data.get("rows", [])],
            response_aggregation_type=data.get("responseAggregationType", ""),
        )


@dataclass
class SitemapContent:
    """A per-content-type breakdown inside a sitemap entry."""

    type: str = ""
    submitted: int = 0
    indexed: int = 0

    @classmethod
    def from_api(cls, data: dict) -> SitemapContent:
        return cls(
            type=data.get("type", ""),
            submitted=int(data.get("submitted", 0)),
            indexed=int(data.get("indexed", 0)),
        )


@dataclass
class Sitemap:
    """A submitted sitemap (``webmasters.sitemaps``)."""

    path: str = ""
    last_submitted: str = ""
    last_downloaded: str = ""
    is_pending: bool = False
    is_sitemaps_index: bool = False
    type: str = ""
    warnings: int = 0
    errors: int = 0
    contents: list[SitemapContent] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> Sitemap:
        return cls(
            path=data.get("path", ""),
            last_submitted=data.get("lastSubmitted", ""),
            last_downloaded=data.get("lastDownloaded", ""),
            is_pending=bool(data.get("isPending", False)),
            is_sitemaps_index=bool(data.get("isSitemapsIndex", False)),
            type=data.get("type", ""),
            warnings=int(data.get("warnings", 0)),
            errors=int(data.get("errors", 0)),
            contents=[SitemapContent.from_api(c) for c in data.get("contents", [])],
        )


@dataclass
class IndexStatus:
    """The index-status verdict for a URL inspection result."""

    verdict: str = ""
    coverage_state: str = ""
    robots_txt_state: str = ""
    indexing_state: str = ""
    page_fetch_state: str = ""
    google_canonical: str = ""
    user_canonical: str = ""
    last_crawl_time: str = ""

    @classmethod
    def from_api(cls, data: dict) -> IndexStatus:
        return cls(
            verdict=data.get("verdict", ""),
            coverage_state=data.get("coverageState", ""),
            robots_txt_state=data.get("robotsTxtState", ""),
            indexing_state=data.get("indexingState", ""),
            page_fetch_state=data.get("pageFetchState", ""),
            google_canonical=data.get("googleCanonical", ""),
            user_canonical=data.get("userCanonical", ""),
            last_crawl_time=data.get("lastCrawlTime", ""),
        )


@dataclass
class InspectionResult:
    """The result of a URL inspection (``urlInspection.index.inspect``)."""

    inspection_result_link: str = ""
    index_status: IndexStatus | None = None

    @classmethod
    def from_api(cls, data: dict) -> InspectionResult:
        result = data.get("inspectionResult", data)
        index_status_data = result.get("indexStatusResult")
        return cls(
            inspection_result_link=result.get("inspectionResultLink", ""),
            index_status=(IndexStatus.from_api(index_status_data) if index_status_data else None),
        )


@dataclass
class Profile:
    """A stored auth profile from ``config.yaml``."""

    name: str
    auth_type: str = "oauth2"
    credentials: str = ""
    sites: list[str] = field(default_factory=list)

    @property
    def is_oauth(self) -> bool:
        return self.auth_type == "oauth2"

    @property
    def is_service_account(self) -> bool:
        return self.auth_type == "service_account"

    @classmethod
    def from_api(cls, data: dict) -> Profile:
        return cls(
            name=data.get("name", ""),
            auth_type=data.get("auth_type", "oauth2"),
            credentials=data.get("credentials", ""),
            sites=list(data.get("sites", [])),
        )
