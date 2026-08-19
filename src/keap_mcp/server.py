import contextvars
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .api_client import KeapClient
from .config import Settings

_HEADER_NAME = "X-Keap-Access-Token"

# Per-request credential isolation via contextvars.
# GatewayTokenMiddleware sets this before the MCP handler runs.
# Python asyncio copies context per task, so concurrent SSE connections are isolated.
_gateway_token_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "keap_gateway_token", default=None
)


def get_client_from_context(settings: Settings) -> KeapClient | None:
    """Resolve the active KeapClient for the current request context.

    Credentials come exclusively from the per-request contextvar set by
    GatewayTokenMiddleware (i.e. from the incoming HTTP header) — there is
    intentionally no environment-variable fallback here, since this process
    serves multiple tenants concurrently and a fallback would risk one
    tenant's calls silently using another tenant's (or a shared dev) token.
    """
    token = _gateway_token_var.get()
    if not token:
        return None
    return KeapClient(token)


class GatewayTokenMiddleware:
    """ASGI middleware.

    Reads X-Keap-Access-Token (required) from request headers and stores it
    in the contextvar. Returns 401 if the header is missing on /mcp requests.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        token = request.headers.get(_HEADER_NAME.lower())
        if not token:
            response = JSONResponse(
                {
                    "error": "Missing credentials",
                    "message": f"This server requires the {_HEADER_NAME} header",
                    "required_headers": [_HEADER_NAME],
                    "optional_headers": [],
                },
                status_code=401,
            )
            await response(scope, receive, send)
            return

        ctx_token = _gateway_token_var.set(token)
        try:
            await self.app(scope, receive, send)
        finally:
            _gateway_token_var.reset(ctx_token)


def create_mcp_server(settings: Settings) -> FastMCP:
    """Build the FastMCP server instance and register all Keap tools."""
    # DNS-rebinding protection is a browser-oriented safeguard that rejects
    # non-localhost Host headers with 421. Disable it so the server works
    # correctly behind a reverse proxy or docker network.
    mcp = FastMCP(
        name="keap-mcp",
        instructions=(
            "Keap (formerly Infusionsoft) is a CRM and marketing-automation "
            "platform for small businesses, built around Contacts. Core "
            "concepts: Contacts (people/leads); Tags (labels for "
            "segmentation); Opportunities (sales deals moving through "
            "pipeline Stages, owned by a User); Notes (freeform records "
            "attached to a Contact); Tasks (to-dos, optionally linked to a "
            "Contact and assigned to a User); Campaigns "
            "(marketing/automation sequences); Users (staff who own "
            "Opportunities/Tasks).\n\n"
            "Typical flow: find a contact with keap_list_contacts or "
            "keap_get_contact, then use its contact_id to list/apply tags "
            "(keap_list_contact_tags, keap_apply_tags_to_contact), or "
            "list/create its opportunities, notes, and tasks "
            "(keap_list_opportunities, keap_create_opportunity, "
            "keap_list_notes, keap_create_note, keap_list_tasks, "
            "keap_create_task). keap_list_tags and keap_list_campaigns are "
            "org-wide lookups for finding IDs before filtering. "
            "keap_list_users lists staff who can own opportunities/tasks.\n\n"
            "All 15 tools are read or additive (list/get/create/apply) - "
            "there are no update or delete tools in this service."
        ),
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )

    client_factory: Callable[[], KeapClient | None] = lambda: get_client_from_context(settings)

    from .tools import crm

    crm.register(mcp, client_factory)

    return mcp
