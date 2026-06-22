"""
Security-headers middleware for the rag-expertchat app.

This app stores user-uploaded documents and serves a chat UI on a domain whose
reputation matters, so the headers here are deliberately defensive. Django's own
SecurityMiddleware handles X-Content-Type-Options, Referrer-Policy and (optionally)
HSTS via SECURE_* settings; the XFrameOptionsMiddleware handles X-Frame-Options.
This middleware adds the headers Django does not provide out of the box:

  * Content-Security-Policy-Report-Only (NON-enforcing) with a per-request nonce.
    Report-Only blocks nothing - it lets us collect violations before promoting
    to an enforcing policy in a later change.
  * Permissions-Policy - lock off camera / microphone / geolocation (no voice
    input feature exists in the chat).
  * Cross-Origin-Opener-Policy: same-origin - the chat has no cross-origin popup
    / window.opener flow.
  * Strips any X-Powered-By the app layer might emit (version disclosure).

The per-request nonce is exposed as ``request.csp_nonce`` so templates that already
reference ``{{ request.csp_nonce }}`` on their <script>/<link> tags line up with the
nonce advertised in the CSP header.
"""

import secrets


# CDN / external origins the templates and client bundle actually load from.
# Enumerated from aichat_users/templates/aichat_users/layout.html and the static JS.
_SCRIPT_SRC = (
    "https://cdn.jsdelivr.net "        # bootstrap bundle, DOMPurify
    "https://cdnjs.cloudflare.com "    # font-awesome, pdf.js
    "https://code.jquery.com "         # jquery (slim)
    "https://ajax.googleapis.com"      # jquery
)
_STYLE_SRC = (
    "https://cdn.jsdelivr.net "        # bootstrap, bootstrap-icons
    "https://cdnjs.cloudflare.com"     # font-awesome
)
_FONT_SRC = (
    "https://cdnjs.cloudflare.com "    # font-awesome webfonts
    "https://cdn.jsdelivr.net"         # bootstrap-icons webfont
)


def _build_csp(nonce):
    """Build a broad, union allow-list CSP (Report-Only)."""
    directives = [
        "default-src 'self'",
        # Nonce + the known CDN origins. 'unsafe-inline'/'unsafe-eval' are kept in
        # the union for broad compatibility while this is Report-Only; CSP3
        # browsers ignore 'unsafe-inline' when a nonce is present, so promoting to
        # enforcing later (dropping the unsafe-* tokens) is a one-line change.
        f"script-src 'self' 'nonce-{nonce}' 'unsafe-inline' 'unsafe-eval' {_SCRIPT_SRC}",
        f"style-src 'self' 'unsafe-inline' {_STYLE_SRC}",
        f"font-src 'self' data: {_FONT_SRC}",
        # Expert photos and uploaded-image previews can be remote; allow https/data.
        "img-src 'self' data: https:",
        # The chat stream endpoint (EventSource) and all fetch() calls are
        # same-origin; the LLM API is called server-side, never from the browser.
        "connect-src 'self'",
        "worker-src 'self' blob:",      # pdf.js worker
        "frame-ancestors 'none'",       # mirrors X-Frame-Options: DENY
        "base-uri 'self'",
        "form-action 'self'",
        "object-src 'none'",
    ]
    return "; ".join(directives)


class SecurityHeadersMiddleware:
    """Adds CSP-Report-Only, Permissions-Policy and COOP to every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate the nonce before the view/template render so {{ request.csp_nonce }}
        # resolves to the same value advertised in the CSP header below.
        nonce = secrets.token_urlsafe(16)
        request.csp_nonce = nonce

        response = self.get_response(request)

        response.setdefault("Content-Security-Policy-Report-Only", _build_csp(nonce))
        response.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        # Remove any app-layer version disclosure.
        if "X-Powered-By" in response:
            del response["X-Powered-By"]

        return response
