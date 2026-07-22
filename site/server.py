#!/usr/bin/env python3
"""Minimal Railway server for the standalone portfolio."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import base64
import html
import os
import re


ROOT = Path(__file__).resolve().parent
HTML_TEMPLATE = (ROOT / "index.html").read_text(encoding="utf-8")
OG_IMAGE = (ROOT / "public" / "og-endpoint-agentic.png").read_bytes()
TEXT_ASSETS = {
    "/robots.txt": ("text/plain; charset=utf-8", (ROOT / "public" / "robots.txt").read_text(encoding="utf-8")),
    "/llms.txt": ("text/plain; charset=utf-8", (ROOT / "public" / "llms.txt").read_text(encoding="utf-8")),
    "/llms-full.txt": ("text/plain; charset=utf-8", (ROOT / "public" / "llms-full.txt").read_text(encoding="utf-8")),
    "/proof.json": ("application/json; charset=utf-8", (ROOT / "public" / "proof.json").read_text(encoding="utf-8")),
    "/sitemap.xml": ("application/xml; charset=utf-8", (ROOT / "public" / "sitemap.xml").read_text(encoding="utf-8")),
    "/security.txt": ("text/plain; charset=utf-8", (ROOT / "public" / "security.txt").read_text(encoding="utf-8")),
    "/.well-known/security.txt": ("text/plain; charset=utf-8", (ROOT / "public" / "security.txt").read_text(encoding="utf-8")),
}
MACHINE_READABLE_PATHS = {"/robots.txt", "/llms.txt", "/llms-full.txt", "/proof.json"}

HOST_PATTERN = re.compile(r"^(?:[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?|\[[0-9a-f:]+\])(?::[0-9]{1,5})?$", re.IGNORECASE)

SECURITY_HEADERS = {
    "Cross-Origin-Opener-Policy": "same-origin",
    "Origin-Agent-Cluster": "?1",
    "Permissions-Policy": "accelerometer=(), camera=(), display-capture=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Download-Options": "noopen",
    "X-Frame-Options": "DENY",
    "X-Permitted-Cross-Domain-Policies": "none",
    "X-Portfolio-Invariant": "models-propose;systems-verify;humans-decide",
}

HTML_CSP = (
    "default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; "
    "img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; "
    "object-src 'none'; upgrade-insecure-requests"
)
ASSET_CSP = (
    "default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; "
    "object-src 'none'; upgrade-insecure-requests"
)


class PortfolioHandler(BaseHTTPRequestHandler):
    server_version = "Portfolio"
    sys_version = ""

    def _origin(self) -> str:
        configured_host = os.environ.get("PUBLIC_DOMAIN") or os.environ.get("RAILWAY_PUBLIC_DOMAIN")
        if configured_host:
            configured_host = configured_host.strip().lower()
            if HOST_PATTERN.fullmatch(configured_host):
                return f"https://{configured_host}"

        host = (self.headers.get("Host") or "localhost").split(",", 1)[0].strip().lower()
        if not HOST_PATTERN.fullmatch(host):
            host = "localhost"
        proto = self.headers.get("X-Forwarded-Proto", "http").split(",", 1)[0].strip().lower()
        if proto not in {"http", "https"}:
            proto = "http"
        return f"{proto}://{host}"

    def _send(
        self,
        status: int,
        content_type: str,
        body: bytes,
        cache_control: str = "no-store",
        *,
        nonce: str | None = None,
        indexable: bool = True,
        allow: str | None = None,
        cross_origin: bool = False,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache_control)
        self.send_header("Content-Security-Policy", HTML_CSP.format(nonce=nonce) if nonce else ASSET_CSP)
        self.send_header("X-Robots-Tag", "index, follow" if indexable else "noindex, nofollow, noarchive")
        if allow:
            self.send_header("Allow", allow)
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin" if cross_origin else "same-origin")
        if cross_origin:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        origin = self._origin()
        if path in ("/", "/index.html"):
            nonce = base64.b64encode(os.urandom(18)).decode("ascii")
            safe_origin = html.escape(origin, quote=True)
            page = HTML_TEMPLATE.replace("__SITE_ORIGIN__", safe_origin)
            page = page.replace("<style>", f'<style nonce="{nonce}">', 1)
            page = page.replace('<script type="application/ld+json">', f'<script nonce="{nonce}" type="application/ld+json">', 1)
            self._send(200, "text/html; charset=utf-8", page.encode("utf-8"), nonce=nonce)
            return
        if path == "/healthz":
            self._send(200, "text/plain; charset=utf-8", b"ok\n", indexable=False)
            return
        if path == "/og-endpoint-agentic.png":
            self._send(200, "image/png", OG_IMAGE, "public, max-age=86400, immutable")
            return
        if path in TEXT_ASSETS:
            content_type, template = TEXT_ASSETS[path]
            body = template.replace("__SITE_ORIGIN__", origin).encode("utf-8")
            self._send(200, content_type, body, "public, max-age=3600", cross_origin=path in MACHINE_READABLE_PATHS)
            return
        self._send(404, "text/plain; charset=utf-8", b"Not Found", indexable=False)

    def do_HEAD(self) -> None:
        self.do_GET()

    def _method_not_allowed(self) -> None:
        self._send(405, "text/plain; charset=utf-8", b"Method Not Allowed", indexable=False, allow="GET, HEAD")

    do_POST = _method_not_allowed
    do_PUT = _method_not_allowed
    do_PATCH = _method_not_allowed
    do_DELETE = _method_not_allowed
    do_CONNECT = _method_not_allowed
    do_OPTIONS = _method_not_allowed
    do_TRACE = _method_not_allowed

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        body = b"Not Found" if code == 404 else b"Request Rejected"
        self._send(code, "text/plain; charset=utf-8", body, indexable=False)

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    ThreadingHTTPServer(("0.0.0.0", port), PortfolioHandler).serve_forever()
