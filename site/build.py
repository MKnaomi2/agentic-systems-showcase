#!/usr/bin/env python3
"""Regenerate the standalone page and Sites worker from src/page.html.

src/page.html is the single source of truth (title + style + body markup,
no doctype/html/head/body). This wraps it into the standalone, deployable
index.html. Edit src/page.html, run this, never hand-edit index.html.
"""
from pathlib import Path
import base64
import json

root = Path(__file__).parent
content = (root / "src" / "page.html").read_text(encoding="utf-8")
public_text_paths = {
    "/robots.txt": ("text/plain; charset=utf-8", root / "public" / "robots.txt"),
    "/llms.txt": ("text/plain; charset=utf-8", root / "public" / "llms.txt"),
    "/llms-full.txt": ("text/plain; charset=utf-8", root / "public" / "llms-full.txt"),
    "/proof.json": ("application/json; charset=utf-8", root / "public" / "proof.json"),
    "/sitemap.xml": ("application/xml; charset=utf-8", root / "public" / "sitemap.xml"),
    "/security.txt": ("text/plain; charset=utf-8", root / "public" / "security.txt"),
    "/.well-known/security.txt": ("text/plain; charset=utf-8", root / "public" / "security.txt"),
}
public_text_assets = {
    route: {"contentType": content_type, "template": path.read_text(encoding="utf-8")}
    for route, (content_type, path) in public_text_paths.items()
}

split_at = content.index("</style>") + len("</style>")
head, body = content[:split_at], content[split_at:]

index = (
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    '<meta name="description" content="AJ Chandler is an IT systems engineer and independent AI product builder who ships secure agent applications, full-stack AI products, and governed agent infrastructure.">\n'
    '<meta name="author" content="Alvento AJ Chandler Jr">\n'
    '<meta name="robots" content="index, follow, max-image-preview:large">\n'
    '<link rel="canonical" href="__SITE_ORIGIN__">\n'
    '<link rel="alternate" type="text/plain" href="__SITE_ORIGIN__/llms.txt" title="LLM-readable portfolio summary">\n'
    '<meta property="og:type" content="website">\n'
    '<meta property="og:title" content="AJ Chandler - Systems Engineer Building Secure AI Products">\n'
    '<meta property="og:description" content="Secure AI systems shipped as real products. View live work, architecture, test scope, and safety decisions.">\n'
    '<meta property="og:url" content="__SITE_ORIGIN__">\n'
    '<meta property="og:image" content="__SITE_ORIGIN__/og-endpoint-agentic.png">\n'
    '<meta name="twitter:card" content="summary_large_image">\n'
    '<meta name="twitter:title" content="AJ Chandler - Systems Engineer Building Secure AI Products">\n'
    '<meta name="twitter:description" content="Secure AI systems shipped as real products. View live work, architecture, test scope, and safety decisions.">\n'
    '<meta name="twitter:image" content="__SITE_ORIGIN__/og-endpoint-agentic.png">\n'
    '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Person","name":"Alvento AJ Chandler Jr","alternateName":"AJ Chandler","url":"__SITE_ORIGIN__","email":"mailto:alvento.lisp@proton.me","sameAs":["https://www.linkedin.com/in/alvento-chandler-jr","https://github.com/MKnaomi2","https://github.com/MKnaomi2/agentic-systems-showcase"],"jobTitle":"IT Systems Administrator II","description":"IT systems engineer and independent AI product builder targeting AI systems, agent infrastructure, and AI product engineering roles.","knowsAbout":["Full-stack AI products","Agentic systems","LLM safety","Native application development","Least-privilege automation","AI infrastructure"]}</script>\n'
    + head + "\n</head>\n<body>" + body + "\n</body>\n</html>\n"
)
(root / "index.html").write_text(index, encoding="utf-8")

og_path = root / "public" / "og-endpoint-agentic.png"
og_base64 = base64.b64encode(og_path.read_bytes()).decode("ascii")

worker = f'''const HTML_TEMPLATE = {json.dumps(index)};
const OG_IMAGE_BASE64 = {json.dumps(og_base64)};
const TEXT_ASSETS = {json.dumps(public_text_assets)};
const MACHINE_READABLE_PATHS = new Set(["/robots.txt", "/llms.txt", "/llms-full.txt", "/proof.json"]);

function createNonce() {{
  const bytes = new Uint8Array(18);
  crypto.getRandomValues(bytes);
  return btoa(String.fromCharCode(...bytes));
}}

function securityHeaders({{ nonce = null, indexable = true, crossOrigin = false }} = {{}}) {{
  const csp = nonce
    ? `default-src 'none'; script-src 'nonce-${{nonce}}'; style-src 'nonce-${{nonce}}'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'; upgrade-insecure-requests`
    : "default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'; upgrade-insecure-requests";
  return {{
    "Content-Security-Policy": csp,
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": crossOrigin ? "cross-origin" : "same-origin",
    ...(crossOrigin ? {{ "Access-Control-Allow-Origin": "*" }} : {{}}),
    "Origin-Agent-Cluster": "?1",
    "Permissions-Policy": "accelerometer=(), camera=(), display-capture=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Download-Options": "noopen",
    "X-Frame-Options": "DENY",
    "X-Permitted-Cross-Domain-Policies": "none",
    "X-Portfolio-Invariant": "models-propose;systems-verify;humans-decide",
    "X-Robots-Tag": indexable ? "index, follow" : "noindex, nofollow, noarchive",
  }};
}}

function decodeBase64(value) {{
  return Uint8Array.from(atob(value), (character) => character.charCodeAt(0));
}}

export default {{
  async fetch(request) {{
    const url = new URL(request.url);
    const isHead = request.method === "HEAD";
    if (request.method !== "GET" && !isHead) {{
      return new Response("Method Not Allowed", {{ status: 405, headers: {{ ...securityHeaders({{ indexable: false }}), Allow: "GET, HEAD" }} }});
    }}

    if (url.pathname === "/healthz") {{
      return new Response(isHead ? null : "ok\\n", {{
        headers: {{ ...securityHeaders({{ indexable: false }}), "Cache-Control": "no-store", "Content-Type": "text/plain; charset=utf-8" }},
      }});
    }}

    if (url.pathname === "/og-endpoint-agentic.png") {{
      return new Response(isHead ? null : decodeBase64(OG_IMAGE_BASE64), {{
        headers: {{
          ...securityHeaders(),
          "Cache-Control": "public, max-age=86400, immutable",
          "Content-Type": "image/png",
        }},
      }});
    }}

    if (TEXT_ASSETS[url.pathname]) {{
      const asset = TEXT_ASSETS[url.pathname];
      const body = asset.template.replaceAll("__SITE_ORIGIN__", url.origin);
      return new Response(isHead ? null : body, {{
        headers: {{
          ...securityHeaders({{ crossOrigin: MACHINE_READABLE_PATHS.has(url.pathname) }}),
          "Cache-Control": "public, max-age=3600",
          "Content-Type": asset.contentType,
        }},
      }});
    }}

    if (url.pathname !== "/" && url.pathname !== "/index.html") {{
      return new Response("Not Found", {{ status: 404, headers: securityHeaders({{ indexable: false }}) }});
    }}

    const nonce = createNonce();
    const html = HTML_TEMPLATE
      .replaceAll("__SITE_ORIGIN__", url.origin)
      .replace("<style>", `<style nonce="${{nonce}}">`)
      .replace('<script type="application/ld+json">', `<script nonce="${{nonce}}" type="application/ld+json">`);
    return new Response(isHead ? null : html, {{
      headers: {{ ...securityHeaders({{ nonce }}), "Cache-Control": "no-store", "Content-Type": "text/html; charset=utf-8" }},
    }});
  }},
}};
'''

worker_path = root / "dist" / "server" / "index.js"
worker_path.parent.mkdir(parents=True, exist_ok=True)
worker_path.write_text(worker, encoding="utf-8")

print(f"index.html written ({len(index.encode())} bytes)")
print(f"Sites worker written ({len(worker.encode())} bytes)")
