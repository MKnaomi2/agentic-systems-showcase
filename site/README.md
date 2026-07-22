# Portfolio source snapshot

This directory contains a clean, sanitized snapshot of the source deployed at
[ai.wadevo.com](https://ai.wadevo.com). It has no connection to the private
repository history used to develop the site.

## Build and test

```bash
python build.py
python -m unittest discover -s tests -v
```

`src/page.html` is the source of truth. `build.py` produces the standalone
`index.html` and the Cloudflare Worker-compatible server bundle. `server.py`
provides the hardened read-only Railway surface.

It intentionally omits employer-specific system details, internal metrics,
private contact information, and nonpublic infrastructure.

The tests verify nonce-bound CSP, HSTS, minimal health responses, uniform 404s
for sensitive paths, unsafe-method rejection, structured proof, and regression
protection against employer-specific details or the private contact address.

