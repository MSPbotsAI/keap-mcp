"""tools/list snapshot + error-envelope mapping tests.

No network calls: tool enumeration goes through FastMCP's in-process
list_tools(), and the error-code mapping is tested directly against
KeapError, independent of any real HTTP request.
"""

import pytest

from keap_mcp.api_client import KeapError
from keap_mcp.config import Settings
from keap_mcp.server import create_mcp_server

EXPECTED_TOOLS = {
    "keap_list_contacts": set(),
    "keap_get_contact": {"contact_id"},
    "keap_create_contact": set(),
    "keap_list_contact_tags": {"contact_id"},
    "keap_apply_tags_to_contact": {"contact_id", "tag_ids"},
    "keap_list_tags": set(),
    "keap_list_opportunities": set(),
    "keap_get_opportunity": {"opportunity_id"},
    "keap_create_opportunity": {"contact_id", "stage_id", "opportunity_title"},
    "keap_list_notes": set(),
    "keap_create_note": {"contact_id"},
    "keap_list_tasks": set(),
    "keap_create_task": {"title", "due_date"},
    "keap_list_campaigns": set(),
    "keap_list_users": set(),
}


@pytest.mark.asyncio
async def test_tools_list_snapshot():
    mcp = create_mcp_server(Settings())
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert names == set(EXPECTED_TOOLS), f"unexpected tool set: {names}"

    by_name = {t.name: t for t in tools}
    for name, expected_required in EXPECTED_TOOLS.items():
        tool = by_name[name]
        required = set(tool.inputSchema.get("required", []))
        assert required == expected_required, f"{name}: required={required}"
        assert tool.annotations is not None
        assert len(tool.description or "") <= 500, f"{name}: description too long"
        first_line = (tool.description or "").strip().splitlines()[0]
        assert len(first_line) <= 100, f"{name}: first line too long: {first_line!r}"


def test_read_only_tools_are_annotated_read_only():
    import asyncio

    mcp = create_mcp_server(Settings())
    tools = asyncio.run(mcp.list_tools())
    by_name = {t.name: t for t in tools}

    write_tools = {
        "keap_create_contact",
        "keap_apply_tags_to_contact",
        "keap_create_opportunity",
        "keap_create_note",
        "keap_create_task",
    }
    for name, tool in by_name.items():
        if name in write_tools:
            assert tool.annotations.readOnlyHint is False, f"{name}: expected readOnlyHint=False"
        else:
            assert tool.annotations.readOnlyHint is True, f"{name}: expected readOnlyHint=True"


@pytest.mark.asyncio
async def test_service_instructions_present_and_bounded():
    mcp = create_mcp_server(Settings())
    assert mcp.instructions
    assert len(mcp.instructions) <= 1500


@pytest.mark.parametrize(
    "status_code,expected_code,expected_retryable",
    [
        (0, "upstream_error", True),
        (400, "invalid_argument", False),
        (401, "unauthorized", False),
        (403, "unauthorized", False),
        (404, "not_found", False),
        (422, "invalid_argument", False),
        (429, "rate_limited", True),
        (500, "upstream_error", True),
        (503, "upstream_error", True),
    ],
)
def test_error_envelope_mapping(status_code, expected_code, expected_retryable):
    import json

    err = KeapError(status_code, "boom")
    envelope = json.loads(err.to_envelope())
    assert envelope["error"]["code"] == expected_code
    assert envelope["error"]["retryable"] is expected_retryable
    assert envelope["error"]["message"] == "boom"
