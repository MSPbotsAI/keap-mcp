from .._json import error_envelope

NO_TOKEN = error_envelope(
    "not_configured", "No Keap access token. Send the X-Keap-Access-Token header.", False
)

# SOP token-economy fallback ceiling (Keap's own API accepts up to 1000 per
# page on list endpoints, which is looser than this — we clamp to the
# stricter SOP default/hard-cap since it's the binding limit here).
DEFAULT_LIMIT = 20
MAX_LIMIT = 200
