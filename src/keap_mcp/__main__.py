import sys

from .config import get_settings
from .server import GatewayTokenMiddleware, create_mcp_server


def _build_http_app(mcp, settings):
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "transport": "http", "auth_mode": settings.auth_mode})

    mcp_app = mcp.streamable_http_app()
    mounted = GatewayTokenMiddleware(mcp_app, settings) if settings.auth_mode == "gateway" else mcp_app

    return Starlette(
        routes=[Route("/health", health), Mount("/", app=mounted)],
        lifespan=lambda app: mcp_app.router.lifespan_context(app),
    )


def main() -> None:
    settings = get_settings()
    mcp = create_mcp_server(settings)

    if settings.mcp_transport == "http":
        import uvicorn

        app = _build_http_app(mcp, settings)

        print(
            f"Keap MCP server listening on http://{settings.mcp_http_host}:{settings.mcp_http_port}/mcp",
            file=sys.stderr,
        )
        print(f"Auth mode: {settings.auth_mode}", file=sys.stderr)
        uvicorn.run(app, host=settings.mcp_http_host, port=settings.mcp_http_port)
    else:
        print("Keap MCP server running on stdio", file=sys.stderr)
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
