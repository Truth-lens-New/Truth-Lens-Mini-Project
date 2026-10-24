"""
SSRF regression tests for the URL guard (app/services/input/url_guard.py).

All DNS resolution is mocked; no network is touched.
"""

import socket

import pytest

from import_utils import isolated_imports


@pytest.fixture(scope="module")
def url_guard():
    with isolated_imports(["app", "app.services", "app.services.input"]) as imp:
        yield imp("app.services.input.url_guard")


@pytest.fixture()
def public_dns(monkeypatch):
    """Mock DNS so every hostname (except literals) resolves to a public IP."""
    def fake_getaddrinfo(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)


@pytest.fixture()
def private_dns(monkeypatch):
    """Mock DNS so every hostname resolves into the private address space."""
    def fake_getaddrinfo(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.1.2.3", port))]
    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)


class TestSchemeValidation:
    def test_allows_https(self, url_guard, public_dns):
        assert url_guard.validate_http_url("https://example.com/article") == "https://example.com/article"

    def test_allows_http(self, url_guard, public_dns):
        assert url_guard.validate_http_url("http://example.com/") == "http://example.com/"

    @pytest.mark.parametrize("url", [
        "file:///etc/passwd",
        "ftp://example.com/pub",
        "gopher://example.com",
        "javascript://example.com/alert",
        "data:text/html,hello",
    ])
    def test_rejects_non_http_schemes(self, url_guard, url):
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_http_url(url)

    def test_rejects_empty_url(self, url_guard):
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_http_url("")


class TestCredentialsAndInternalHosts:
    @pytest.mark.parametrize("url", [
        "https://user:password@example.com/",
        "https://admin@malicious.example/",
    ])
    def test_rejects_embedded_credentials(self, url_guard, public_dns, url):
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_http_url(url)

    def test_rejects_localhost(self, url_guard):
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_http_url("http://localhost:8000/api")

    def test_rejects_subdomain_localhost(self, url_guard):
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_http_url("http://evil.localhost/")


class TestLiteralAddresses:
    @pytest.mark.parametrize("url", [
        "http://127.0.0.1/",
        "http://10.0.0.5/",
        "http://172.16.0.1/",
        "http://192.168.1.100/",
        "http://169.254.169.254/latest/meta-data/",   # cloud metadata endpoint
        "http://0.0.0.0/",
        "http://100.64.0.1/",                        # CGNAT range
        "http://255.255.255.255/",
    ])
    def test_rejects_non_public_ipv4_literals(self, url_guard, url):
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_http_url(url)

    def test_rejects_ipv6_loopback_literal(self, url_guard):
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_http_url("http://[::1]/")

    def test_allows_public_literal_ip(self, url_guard):
        assert url_guard.validate_http_url("http://93.184.216.34/page") == "http://93.184.216.34/page"


class TestDNSResolution:
    def test_rejects_hostname_resolving_to_private_ip(self, url_guard, private_dns):
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_http_url("https://example.com/")

    def test_rejects_unresolvable_host(self, url_guard, monkeypatch):
        def fake_getaddrinfo(*args, **kwargs):
            raise socket.gaierror(8, "nodename nor servname provided")
        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_http_url("https://definitely-not-a-real-domain.example/")

    def test_allows_hostname_resolving_to_public_ip(self, url_guard, public_dns):
        assert url_guard.validate_http_url("https://example.com/") == "https://example.com/"


class TestRedirectTargets:
    def test_rejects_redirect_to_private_host(self, url_guard):
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_redirect_target("https://example.com/a", "http://127.0.0.1/admin")

    def test_rejects_redirect_to_other_scheme(self, url_guard):
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_redirect_target("https://example.com/a", "file:///etc/passwd")

    def test_allows_relative_redirect_on_public_origin(self, url_guard, public_dns):
        resolved = url_guard.validate_redirect_target("https://example.com/a/b", "c/d")
        assert resolved == "https://example.com/a/c/d"

    def test_rejects_redirect_to_unresolvable_private_subdomain(self, url_guard, private_dns):
        with pytest.raises(url_guard.UnsafeURLError):
            url_guard.validate_redirect_target(
                "https://example.com/a", "https://internal-only.internal/admin"
            )
