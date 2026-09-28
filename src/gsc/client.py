"""Thin wrapper over the two Google Search Console discovery services."""

from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build

from .models import (
    InspectionResult,
    SearchAnalyticsResponse,
    Site,
    Sitemap,
)


class GSCClient:
    """Wraps ``webmasters`` v3 and ``searchconsole`` v1; methods return models."""

    def __init__(self, credentials: Any) -> None:
        self.credentials = credentials
        self.webmasters = build("webmasters", "v3", credentials=credentials, cache_discovery=False)
        self.searchconsole = build(
            "searchconsole", "v1", credentials=credentials, cache_discovery=False
        )

    def list_sites(self) -> list[Site]:
        response = self.webmasters.sites().list().execute()
        return [Site.from_api(entry) for entry in response.get("siteEntry", [])]

    def get_site(self, site_url: str) -> Site:
        response = self.webmasters.sites().get(siteUrl=site_url).execute()
        return Site.from_api(response)

    def query(self, site_url: str, body: dict) -> SearchAnalyticsResponse:
        response = self.webmasters.searchanalytics().query(siteUrl=site_url, body=body).execute()
        return SearchAnalyticsResponse.from_api(response)

    def list_sitemaps(self, site_url: str) -> list[Sitemap]:
        response = self.webmasters.sitemaps().list(siteUrl=site_url).execute()
        return [Sitemap.from_api(entry) for entry in response.get("sitemap", [])]

    def get_sitemap(self, site_url: str, feedpath: str) -> Sitemap:
        response = self.webmasters.sitemaps().get(siteUrl=site_url, feedpath=feedpath).execute()
        return Sitemap.from_api(response)

    def submit_sitemap(self, site_url: str, feedpath: str) -> None:
        self.webmasters.sitemaps().submit(siteUrl=site_url, feedpath=feedpath).execute()

    def delete_sitemap(self, site_url: str, feedpath: str) -> None:
        self.webmasters.sitemaps().delete(siteUrl=site_url, feedpath=feedpath).execute()

    def inspect_url(self, site_url: str, inspection_url: str) -> InspectionResult:
        body = {"siteUrl": site_url, "inspectionUrl": inspection_url}
        response = self.searchconsole.urlInspection().index().inspect(body=body).execute()
        return InspectionResult.from_api(response)

    @staticmethod
    def build_query_body(
        start_date: str,
        end_date: str,
        dimensions: list[str] | None = None,
        search_type: str | None = None,
        filters: list[dict] | None = None,
        aggregation_type: str | None = None,
        row_limit: int | None = None,
        start_row: int | None = None,
        data_state: str | None = None,
    ) -> dict:
        """Build a searchanalytics request body, omitting unset optional fields.

        ``filters`` are wrapped in a single ``dimensionFilterGroups`` entry with
        ``groupType: "and"``.
        """
        body: dict[str, Any] = {"startDate": start_date, "endDate": end_date}
        if dimensions:
            body["dimensions"] = dimensions
        if search_type:
            body["type"] = search_type
        if filters:
            body["dimensionFilterGroups"] = [{"groupType": "and", "filters": filters}]
        if aggregation_type:
            body["aggregationType"] = aggregation_type
        if row_limit is not None:
            body["rowLimit"] = row_limit
        if start_row is not None:
            body["startRow"] = start_row
        if data_state:
            body["dataState"] = data_state
        return body
