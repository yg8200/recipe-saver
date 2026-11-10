"""Guards for fetching URLs on behalf of a user (SSRF protection)."""
import ipaddress
import socket
from urllib.parse import urlparse


def is_public_http_url(url: str) -> bool:
    """True only for http(s) URLs whose host resolves exclusively to public internet addresses.

    Without this check a page could point its image at http://localhost:5432 or a cloud metadata
    address, and our server would fetch it for them (Server-Side Request Forgery).
    Known limit: DNS could change between this check and the download (DNS rebinding).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, None)}
    except (socket.gaierror, UnicodeError):
        return False
    # is_global is False for private, loopback, link-local and reserved ranges
    return bool(addresses) and all(ipaddress.ip_address(a).is_global for a in addresses)
