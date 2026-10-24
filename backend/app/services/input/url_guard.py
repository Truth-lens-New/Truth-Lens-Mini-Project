"""
URL Security Guard (SSRF protection)

Validates that a URL points to a public, intended HTTP(S) destination before
any fetch is attempted. Stdlib only so it is cheap and unit-testable.

Checks performed:
- Scheme must be http or https (rejects file:, ftp:, gopher:, ...).
- No inline credentials (user:password@host) allowed.
- Host must not be "localhost" variants, and every resolved IP address must be
  a public, unicast address: loopback, private, link-local, multicast,
  reserved, and unspecified ranges are all rejected.

Callers must re-validate every redirect target (see url_scraper.py) so a
trusted-looking first hop cannot bounce the fetch to an internal host.
"""

import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = ("http", "https")

# Hostname literals that must never be fetched even if they resolve publicly.
_FORBIDDEN_HOSTS = {"localhost", "localhost.localdomain", "ip6-localhost", "metadata"}

# Address ranges that are not internet-routable even though stdlib's
# `ip.is_private` misses some of them (e.g. the CGNAT range).
_EXTRA_DISALLOWED_NETWORKS = tuple(
    ipaddress.ip_network(net)
    for net in (
        "100.64.0.0/10",      # Carrier-grade NAT (RFC 6598)
        "198.18.0.0/15",      # Benchmarking (RFC 2544)
    )
)


def _is_disallowed_ip(ip) -> bool:
    """True when the address is loopback/private/link-local/reserved/etc."""
    if (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return True
    return any(ip in network for network in _EXTRA_DISALLOWED_NETWORKS)


class UnsafeURLError(ValueError):
    """Raised when a URL is not a safe public HTTP(S) destination."""


def _check_ip(ip_str: str, hostname: str) -> None:
    """Reject any resolved address that is not a public unicast address."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        raise UnsafeURLError(f"Unparseable resolved address for host: {hostname}")

    if _is_disallowed_ip(ip):
        raise UnsafeURLError(
            f"Refusing to fetch non-public destination ({ip}) for host: {hostname}"
        )


def _parse_literal_ip(value: str):
    """Return the ip_address for a literal-IP string, else None."""
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def validate_http_url(url: str, resolve_dns: bool = True) -> str:
    """
    Validate `url` as a public HTTP(S) destination.

    Args:
        url: The URL to validate.
        resolve_dns: Resolve the hostname and check every returned address
            (set False only for cheap allow-listed cases; the caller must then
            resolve before fetching).

    Returns:
        The validated URL string (unchanged).

    Raises:
        UnsafeURLError: For any unsafe destination. Always ValueError-compatible.
    """
    if not url or not isinstance(url, str):
        raise UnsafeURLError("Empty URL")

    parsed = urlparse(url.strip())

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeURLError(f"Only http(s) URLs are allowed: {url!r}")

    hostname = (parsed.hostname or "").strip().lower()
    if not hostname:
        raise UnsafeURLError(f"URL has no host: {url!r}")

    if parsed.username or parsed.password:
        raise UnsafeURLError(f"URLs with embedded credentials are not allowed: {url!r}")

    if hostname in _FORBIDDEN_HOSTS or hostname.endswith(".localhost"):
        raise UnsafeURLError(f"Refusing to fetch internal host: {hostname}")

    # A literal-IP URL (no DNS lookup needed).
    literal = _parse_literal_ip(hostname)
    if literal is not None:
        if _is_disallowed_ip(literal):
            raise UnsafeURLError(
                f"Refusing to fetch non-public destination ({literal}) for host: {hostname}"
            )
        return url.strip()

    if resolve_dns:
        try:
            infos = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        except socket.gaierror as exc:
            raise UnsafeURLError(f"Could not resolve host {hostname}: {exc}") from exc
        if not infos:
            raise UnsafeURLError(f"Host resolved to nothing: {hostname}")
        for info in infos:
            _check_ip(info[4][0], hostname)

    return url.strip()


def validate_redirect_target(base_url: str, location: str) -> str:
    """
    Resolve a redirect Location header against the current URL and validate it.
    Relative redirects are joined onto the current origin first; the resolved
    absolute URL is then fully re-validated (scheme, credentials, DNS, ranges).
    """
    from urllib.parse import urljoin

    if not location:
        raise UnsafeURLError("Redirect without a Location header")
    return validate_http_url(urljoin(base_url, location.strip()))
