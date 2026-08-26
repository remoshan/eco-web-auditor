"""Async web scraper: fetches a page's HTML, parses it with BeautifulSoup to
find external assets, then sizes each one concurrently (HEAD -> Range-GET ->
skip) before handing everything off to the carbon calculation.
"""

import asyncio
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)

BROWSER_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
}

MAX_CONCURRENT_ASSET_REQUESTS: int = 12


def to_absolute_url(base_url: str, raw_url: str) -> Optional[str]:
    if not raw_url:
        return None

    raw_url = raw_url.strip()

    for scheme in ("data:", "blob:", "#", "javascript:", "mailto:", "tel:"):
        if raw_url.startswith(scheme):
            return None

    absolute = urljoin(base_url, raw_url)
    parsed = urlparse(absolute)

    if parsed.scheme not in ("http", "https"):
        return None

    return absolute


def extract_assets_from_html(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    assets: list[dict] = []
    seen_urls: set[str] = set()

    def add(url: str, asset_type: str) -> None:
        absolute = to_absolute_url(base_url, url)
        if absolute and absolute not in seen_urls:
            seen_urls.add(absolute)
            assets.append({"url": absolute, "asset_type": asset_type})

    for tag in soup.find_all("img"):
        if src := tag.get("src"):
            add(src, "image")
        if srcset := tag.get("srcset"):
            for part in srcset.split(","):
                candidate = part.strip().split()[0]
                add(candidate, "image")

    for tag in soup.find_all("script", src=True):
        add(tag["src"], "script")

    for tag in soup.find_all("link"):
        rel = tag.get("rel", [])
        if isinstance(rel, str):
            rel = [rel]
        rel_lower = [r.lower() for r in rel]

        href = tag.get("href", "")
        as_attr = tag.get("as", "").lower()

        if "stylesheet" in rel_lower:
            add(href, "css")
        elif "preload" in rel_lower and as_attr == "font":
            add(href, "font")
        elif "preload" in rel_lower and as_attr in ("script",):
            add(href, "script")
        elif "preload" in rel_lower and as_attr in ("style",):
            add(href, "css")
        elif "preload" in rel_lower and as_attr in ("image",):
            add(href, "image")
        elif any(r in rel_lower for r in ("icon", "shortcut icon", "apple-touch-icon")):
            add(href, "image")

    for style_tag in soup.find_all("style"):
        import re
        for url_match in re.finditer(r"url\(['\"]?(https?://[^'\")\s]+)['\"]?\)", style_tag.get_text()):
            url = url_match.group(1)
            ext = url.split("?")[0].lower()
            if any(ext.endswith(f) for f in (".woff2", ".woff", ".ttf", ".otf", ".eot")):
                add(url, "font")

    return assets


async def fetch_asset_info(client: httpx.AsyncClient, asset: dict) -> dict:
    url = asset["url"]
    asset_type = asset["asset_type"]
    size_bytes = 0
    content_type = ""

    try:
        head = await client.head(
            url,
            headers=BROWSER_HEADERS,
            timeout=8.0,
            follow_redirects=True,
        )
        content_type = head.headers.get("content-type", "").split(";")[0].strip()
        raw_length = head.headers.get("content-length")

        if raw_length and raw_length.isdigit():
            size_bytes = int(raw_length)

        else:
            # Some servers omit Content-Length on HEAD; a 1-byte range GET
            # still reveals the full size via Content-Range.
            rng = await client.get(
                url,
                headers={**BROWSER_HEADERS, "Range": "bytes=0-0"},
                timeout=8.0,
                follow_redirects=True,
            )
            cr = rng.headers.get("content-range", "")
            if "/" in cr:
                total_str = cr.split("/")[-1]
                if total_str.isdigit():
                    size_bytes = int(total_str)
            ct = rng.headers.get("content-type", "")
            if ct:
                content_type = ct.split(";")[0].strip()

    except Exception as exc:
        logger.debug("Could not size asset %s: %s", url, exc)

    refined_type = _refine_asset_type(asset_type, content_type)

    path_part = urlparse(url).path.rstrip("/")
    filename = path_part.split("/")[-1].split("?")[0] or "unknown"

    return {
        "url": url,
        "name": filename,
        "asset_type": refined_type,
        "size_bytes": size_bytes,
        "content_type": content_type,
    }


def _refine_asset_type(guessed_type: str, content_type: str) -> str:
    ct = content_type.lower()
    if "image" in ct:
        return "image"
    if "javascript" in ct or "ecmascript" in ct:
        return "script"
    if "css" in ct:
        return "css"
    if "font" in ct or ct.endswith(("/woff2", "/woff", "/otf", "/ttf")):
        return "font"
    if "video" in ct or "audio" in ct:
        return "media"
    return guessed_type


async def scrape_page(url: str) -> dict:
    """
    Raises ValueError for any network/HTTP-level error (caller converts to a 422).
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_ASSET_REQUESTS)

    async with httpx.AsyncClient(verify=True, timeout=settings.SCRAPER_TIMEOUT) as client:

        try:
            response = await client.get(
                url, headers=BROWSER_HEADERS, follow_redirects=True
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ValueError(
                f"Server returned HTTP {exc.response.status_code} for {url}."
            )
        except httpx.ConnectError:
            raise ValueError(
                f"Could not connect to {url}. "
                "Please check the URL and your internet connection."
            )
        except httpx.TimeoutException:
            raise ValueError(f"Request timed out for {url}. Try again shortly.")
        except Exception as exc:
            raise ValueError(f"Failed to fetch {url}: {exc}")

        html_content = response.text
        html_size = len(response.content)
        base_url = str(response.url)

        logger.info("Fetched %s  HTML size: %d bytes", base_url, html_size)

        raw_assets = extract_assets_from_html(html_content, base_url)
        total_found = len(raw_assets)
        raw_assets = raw_assets[: settings.MAX_ASSETS_PER_PAGE]

        logger.info(
            "Found %d assets (capped at %d)", total_found, settings.MAX_ASSETS_PER_PAGE
        )

        async def bounded_fetch(asset: dict) -> dict:
            async with semaphore:
                return await fetch_asset_info(client, asset)

        tasks = [bounded_fetch(a) for a in raw_assets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        assets = [
            r
            for r in results
            if isinstance(r, dict) and r.get("size_bytes", 0) > 0
        ]

    logger.info("Sized %d / %d assets successfully.", len(assets), len(raw_assets))

    return {
        "base_url": base_url,
        "html_size": html_size,
        "assets": assets,
        "total_assets_found": total_found,
    }
