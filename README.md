# keap-mcp

Keap (formerly Infusionsoft) MCP Service — a stateless HTTP MCP server wrapping the [Keap CRM REST API v1](https://developer.keap.com/docs/rest/), covering Contacts, Tags, Opportunities, Notes, Tasks, Campaigns, and Users.

**Tech stack:** Python 3.12 + uv + FastMCP (Starlette/Uvicorn)

It follows the MSPbots **Vendor MCP Service SOP**: stateless, no stored credentials, per-request header authentication only (no environment-variable fallback).

## Scope

Out of Keap's full REST API v1, this service implements **15 tools** aligned to the resource categories MSPbots has historically synced (Contact, Tag Contact, Tags, Opportunities, Notes, Task, Campaigns, User).

## Authentication

Keap's REST API v1 is `oauth2` on paper (`authorization_code` grant is the only flow in its official OpenAPI spec's `securitySchemes`), but Keap also offers a documented, self-service alternative that needs no redirect: **Personal Access Tokens (PAT)** and **Service Account Keys (SAK)** — see [developer.infusionsoft.com/pat-and-sak](https://developer.infusionsoft.com/pat-and-sak/). Either is generated inside the Keap app itself (Settings → API Settings, no developer-app registration or client secret needed) and used as a plain bearer token:

```
Authorization: Bearer <PAT or SAK>
```

This service uses that path — a single static token per tenant, no login/token-exchange step, no redirect. A Service Account Key (admin-level) is recommended over a Personal Access Token (single-user-scoped) for server-to-server use.

Every request to `/mcp` must include the following HTTP header. The token is read **only** from this header on every request (via a request-scoped `contextvar`) — it is never cached, never falls back to an environment variable, and is discarded as soon as the request completes, so concurrent requests from different tenants can never see each other's credentials.

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

The server starts on `http://localhost:8080`.

### Local (uv)

```bash
uv sync
python -m keap_mcp
```

## Health Check

```bash
curl http://localhost:8080/health
# {"status": "ok"}
```

No credentials are required for the health endpoint.

## HEADER 授权参数说明

| Header | 类型 | 是否必填 | 默认值 | 枚举值 | 字段描述 | Example |
|---|---|---|---|---|---|---|
| `X-Keap-Access-Token` | string | 是 | 无 | 无 | Keap Personal Access Token 或 Service Account Key(Keap 后台 Settings → API Settings 生成),本服务原样转发为 `Authorization: Bearer` | `KeapAK-a1b2c3d4e5f6g7h8i9j0` |

Missing the header returns `401 Unauthorized` with the required header name listed in the response body.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_HTTP_PORT` | `8080` | Listening port |
| `MCP_HTTP_HOST` | `0.0.0.0` | Listening host |

No credential fields exist in configuration — the access token is never read from an environment variable in this service; it comes exclusively from the `X-Keap-Access-Token` request header (see above).

## MCP Endpoint

```
POST http://localhost:8080/mcp
```

Connect your MCP client with:
- Transport: `http` (Streamable HTTP)
- Headers: `X-Keap-Access-Token: <token>` (required)

## Available Tools (15)

`limit` parameters below default to 20 and are clamped server-side to a hard cap of 200 (Keap's own API accepts up to 1000 per page, but this service applies the stricter MSPbots token-economy ceiling).

| Tool | Description | API |
|---|---|---|
| `keap_list_contacts` | List contacts | `GET /contacts` |
| `keap_get_contact` | Retrieve a contact by ID | `GET /contacts/{id}` |
| `keap_create_contact` | Create a contact | `POST /contacts` |
| `keap_list_contact_tags` | List tags applied to a contact | `GET /contacts/{contactId}/tags` |
| `keap_apply_tags_to_contact` | Apply tags to a contact | `POST /contacts/{contactId}/tags` |
| `keap_list_tags` | List all tags defined in the app | `GET /tags` |
| `keap_list_opportunities` | List sales opportunities (deals) | `GET /opportunities` |
| `keap_get_opportunity` | Retrieve an opportunity by ID | `GET /opportunities/{opportunityId}` |
| `keap_create_opportunity` | Create a sales opportunity | `POST /opportunities` |
| `keap_list_notes` | List notes | `GET /notes` |
| `keap_create_note` | Create a note on a contact | `POST /notes` |
| `keap_list_tasks` | List tasks | `GET /tasks` |
| `keap_create_task` | Create a task | `POST /tasks` |
| `keap_list_campaigns` | List marketing/automation campaigns | `GET /campaigns` |
| `keap_list_users` | List users of the Keap app | `GET /users` |

Tool descriptions in the MCP protocol itself are intentionally short (business-facing "what it does" summary only); full per-parameter documentation lives in each parameter's JSON-schema `description` (visible via `tools/list`), not in this table.

## 测试示例 (Test Example)

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "X-Keap-Access-Token: <token>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": { "name": "keap_list_contacts", "arguments": { "limit": 5 } }
  }'
```

## Known Gaps

- **⚠️ Not yet tested against a live Keap account.** All 15 tools have been checked structurally only (MCP handshake, tools-list, schema validity, `/health`, gateway 401 credential-gating) — no real PAT/SAK was available at build time. A free-trial Keap account application has been submitted separately; once approved, generate a Service Account Key and test end-to-end.
- Endpoint paths/params were verified directly against Keap's official OpenAPI v1 spec (`https://crm.infusionsoft.com/app/v3/api-docs/V1`, linked from the "Download OpenAPI specification" button on the docs site) — not guessed.
- `PUT /contacts` (upsert) documents a `duplicate_option` field in prose but it does not appear in the actual request schema — a documentation/schema mismatch on Keap's side, not implemented here since it's unconfirmed. Not built as a tool in this 15-tool scope anyway (only `POST`/`GET` contact operations were included).
- Scope is limited to the 15 operations above (Contacts/Tags/Opportunities/Notes/Tasks/Campaigns/Users read+core-write), not Keap's full REST API v1 surface (which also includes Companies, Products, Orders/Subscriptions, Affiliates, Files, Email sending, custom fields management, and webhooks).
- Keap's list endpoints accept `limit` up to 1000 server-side; this service clamps to 200 (the SOP's hard cap) to bound response size and token cost — a value between 200 and 1000 will silently be reduced to 200 rather than rejected.

## API Reference

- [Keap REST API v1 Documentation](https://developer.keap.com/docs/rest/)
- [Personal Access Tokens & Service Account Keys](https://developer.infusionsoft.com/pat-and-sak/)
