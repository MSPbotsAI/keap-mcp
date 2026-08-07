import contextvars
import sys
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .api_client import KeapClient
from .config import Settings

_gateway_token_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "keap_gateway_token", default=None
)


def get_client_from_context(settings: Settings) -> KeapClient | None:
    if settings.auth_mode == "gateway":
        token = _gateway_token_var.get()
    else:
        token = settings.keap_access_token

    if not token:
        return None
    return KeapClient(token)


class GatewayTokenMiddleware:
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
        token = request.headers.get(self.settings.keap_access_token_header.lower())
        if not token:
            response = JSONResponse(
                {
                    "error": "Missing credentials",
                    "message": f"Gateway mode requires the {self.settings.keap_access_token_header} header",
                    "required_headers": [self.settings.keap_access_token_header],
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
    mcp = FastMCP(
        name="keap-mcp",
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )

    client_factory: Callable[[], KeapClient | None] = lambda: get_client_from_context(settings)

    if not settings.has_credentials:
        @mcp.tool()
        async def keap_test_connection() -> str:
            """Test Keap API connection. Shows configuration requirements when credentials are missing."""
            return (
                "Error: Missing Keap credentials.\n\n"
                "Set the required environment variable:\n"
                "  KEAP_ACCESS_TOKEN=your_personal_access_token_or_service_account_key\n\n"
                "Or use gateway mode (per-request token):\n"
                "  AUTH_MODE=gateway\n"
                f"  Send header: {settings.keap_access_token_header}: your_token"
            )

        print("Warning: No Keap credentials found. Only the diagnostic tool is available.", file=sys.stderr)
        return mcp

    from .tools import crm

    crm.register(mcp, client_factory)

    return mcp
