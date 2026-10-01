import asyncio
import contextlib
import ipaddress
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings

GREEN_CHECK_URL = "https://api.thegreenwebfoundation.org/api/v3/greencheck/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
PRELOAD_TYPES = {"font": "font", "script": "script", "style": "css", "image": "image"}
FONT_URL = re.compile(r"url\(['\"]?(https?://[^'\")\s]+\.(?:woff2?|ttf|otf|eot)(?:\?[^'\")\s]*)?)['\"]?\)", re.I)
CONTENT_TYPES = [("image", "image"), ("javascript", "script"), ("ecmascript", "script"), ("css", "css"),
                 ("font", "font"), ("woff", "font"), ("ttf", "font"), ("otf", "font"), ("video", "media"),
                 ("audio", "media")]


class BlockedURLError(ValueError):
    pass


async def reject_private_hosts(request: httpx.Request) -> None:
    if settings.ALLOW_PRIVATE_URLS:
        return
    host = request.url.host
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(host, request.url.port or 443)
    except OSError:
        raise BlockedURLError(f"Could not resolve {host}.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not (getattr(ip, "ipv4_mapped", None) or ip).is_global:
            raise BlockedURLError(f"{host} points to a private or reserved address and can't be audited.")


def extract_assets(html: str, base_url: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    assets: dict[str, str] = {}

    def add(url: str, asset_type: str) -> None:
        url = url.strip()
        absolute = urljoin(base_url, url)
        if url and not url.startswith("#") and urlparse(absolute).scheme in ("http", "https"):
            assets.setdefault(absolute, asset_type)

    for tag in soup.find_all("img"):
        add(tag.get("src", ""), "image")
        for candidate in tag.get("srcset", "").split(","):
            add((candidate.split() or [""])[0], "image")
    for tag in soup.find_all("script", src=True):
        add(tag["src"], "script")
    for tag in soup.find_all("link", href=True):
        rel = [r.lower() for r in tag.get("rel", [])]
        if "stylesheet" in rel:
            add(tag["href"], "css")
        elif "preload" in rel and tag.get("as", "").lower() in PRELOAD_TYPES:
            add(tag["href"], PRELOAD_TYPES[tag["as"].lower()])
        elif "icon" in rel or "apple-touch-icon" in rel:
            add(tag["href"], "image")
    for style in soup.find_all("style"):
        for match in FONT_URL.finditer(style.get_text()):
            add(match.group(1), "font")
    return assets


async def size_asset(client: httpx.AsyncClient, url: str, asset_type: str) -> dict:
    size, content_type = 0, ""
    with contextlib.suppress(Exception):
        response = await client.head(url, timeout=8)
        length = response.headers.get("content-length", "")
        if not length.isdigit():
            response = await client.get(url, headers={"Range": "bytes=0-0"}, timeout=8)
            length = response.headers.get("content-range", "").rpartition("/")[2]
        size = int(length) if length.isdigit() else 0
        content_type = response.headers.get("content-type", "").lower()
    asset_type = next((kind for key, kind in CONTENT_TYPES if key in content_type), asset_type)
    return {"url": url, "name": urlparse(url).path.rstrip("/").split("/")[-1] or "unknown", "asset_type": asset_type,
            "size_bytes": size}


async def check_green_hosting(url: str) -> dict | None:
    with contextlib.suppress(Exception):
        async with httpx.AsyncClient(timeout=5) as client:
            data = (await client.get(GREEN_CHECK_URL + urlparse(url).hostname)).raise_for_status().json()
            return {"green": bool(data["green"]), "hosted_by": data.get("hosted_by")}
    return None


async def scrape_page(url: str) -> dict:
    semaphore = asyncio.Semaphore(12)
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=settings.SCRAPER_TIMEOUT,
                                 event_hooks={"request": [reject_private_hosts]}) as client:
        try:
            response = (await client.get(url)).raise_for_status()
        except BlockedURLError:
            raise
        except httpx.HTTPStatusError as exc:
            raise ValueError(f"Server returned HTTP {exc.response.status_code} for {url}.")
        except httpx.ConnectError:
            raise ValueError(f"Could not connect to {url}. Please check the URL and your internet connection.")
        except httpx.TimeoutException:
            raise ValueError(f"Request timed out for {url}. Try again shortly.")
        except Exception as exc:
            raise ValueError(f"Failed to fetch {url}: {exc}")

        async def bounded(asset_url: str, asset_type: str) -> dict:
            async with semaphore:
                return await size_asset(client, asset_url, asset_type)

        found = list(extract_assets(response.text, str(response.url)).items())[:settings.MAX_ASSETS_PER_PAGE]
        sized = await asyncio.gather(*(bounded(u, t) for u, t in found))
    return {"html_size": len(response.content), "assets": [a for a in sized if a["size_bytes"]]}
