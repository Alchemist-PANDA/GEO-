"""Bounded, server-side public evidence collection for GEO audits.

This module deliberately collects only public HTML from an explicitly supplied
URL. It does not claim that a crawl proves ranking, traffic, reviews, or
ownership. The returned fields are evidence inputs for later interpretation.
"""

from __future__ import annotations

import ipaddress
import json
import socket
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

MAX_BODY_BYTES = 1_000_000
DEFAULT_TIMEOUT_SECONDS = 10


def _public_host(hostname: str) -> bool:
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, None)}
    except (OSError, socket.gaierror):
        return False
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


def validate_public_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("website_url must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.port not in {None, 80, 443}:
        raise ValueError("website_url must not contain credentials or a non-standard port")
    if not _public_host(parsed.hostname):
        raise ValueError("website_url must resolve to a public host")
    return parsed.geturl()


def _schema_types(json_ld: list[object]) -> list[str]:
    types: set[str] = set()
    for item in json_ld:
        if not isinstance(item, dict):
            continue
        values = item.get("@type", [])
        if isinstance(values, str):
            types.add(values)
        elif isinstance(values, list):
            types.update(str(value) for value in values if value)
        graph = item.get("@graph")
        if isinstance(graph, list):
            types.update(_schema_types(graph))
    return sorted(types)


def crawl_public_evidence(url: str, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Fetch and parse one public page with bounded size and explicit provenance."""
    normalized_url = validate_public_url(url)
    response = requests.get(
        normalized_url,
        headers={"User-Agent": "BrandSightGEO/1.0 (+public-evidence-audit)"},
        timeout=timeout,
        stream=True,
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type.lower():
        raise ValueError("website_url did not return an HTML document")

    body = bytearray()
    for chunk in response.iter_content(chunk_size=16_384):
        body.extend(chunk)
        if len(body) > MAX_BODY_BYTES:
            raise ValueError("website response exceeded the 1 MB audit limit")

    soup = BeautifulSoup(bytes(body), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    json_ld: list[object] = []
    for tag in BeautifulSoup(bytes(body), "html.parser").find_all("script", type="application/ld+json"):
        try:
            parsed = json.loads(tag.string or "")
            json_ld.extend(parsed if isinstance(parsed, list) else [parsed])
        except (TypeError, ValueError, json.JSONDecodeError):
            continue

    links = [urljoin(normalized_url, link.get("href")) for link in soup.find_all("a", href=True)]
    text = " ".join(soup.get_text(" ").split())
    source = {
        "url": normalized_url,
        "status_code": response.status_code,
        "content_type": content_type,
        "title": soup.title.get_text(" ", strip=True) if soup.title else "",
        "meta_description": (soup.find("meta", attrs={"name": "description"}) or {}).get("content", ""),
        "h1": [heading.get_text(" ", strip=True) for heading in soup.find_all("h1")],
        "text_length": len(text),
        "schema_types": _schema_types(json_ld),
        "canonical": (soup.find("link", rel="canonical") or {}).get("href"),
        "social_links": [link for link in links if any(host in link for host in ("facebook.com", "instagram.com", "linkedin.com", "youtube.com", "tiktok.com"))],
        "contact_signals": {
            "email": "mailto:" in " ".join(links).lower() or "@" in text,
            "phone": any(token in text.lower() for token in ("phone", "call us", "whatsapp", "+92")),
            "address": any(token in text.lower() for token in ("address", "lahore", "karachi", "islamabad", "pakistan")),
        },
        "evidence_urls": sorted({normalized_url, *(link for link in links if link.startswith(("http://", "https://")))}),
    }
    return source
