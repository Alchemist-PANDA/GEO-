"""SSRF guard for server-side fetches of user/competitor-supplied URLs.

Blocks non-http(s) schemes and any URL that resolves to a private,
loopback, link-local (incl. cloud metadata 169.254.169.254), or reserved
address. Use ``validate_public_url`` before any ``requests.get`` on a URL the
caller does not fully control.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeURLError(ValueError):
    """Raised when a URL is not safe to fetch server-side."""


def _is_public_ip(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"cannot resolve host {host!r}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return False
    return True


def validate_public_url(url: str) -> str:
    """Return the URL if safe to fetch, else raise UnsafeURLError."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeURLError(f"scheme {parsed.scheme!r} not allowed")
    if not parsed.hostname:
        raise UnsafeURLError("missing host")
    if not _is_public_ip(parsed.hostname):
        raise UnsafeURLError(f"host {parsed.hostname!r} resolves to a private/reserved address")
    return url
