"""Keap (Infusionsoft) CRM tools: Contacts, Tags, Opportunities, Notes, Tasks, Campaigns, Users.

Tool naming convention: keap_<action>_<resource>
"""

from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import KeapClient, KeapError
from ._common import MAX_LIMIT, NO_TOKEN

_LIMIT_DESC = "Max results per page (default 20, hard cap 200)."


def _clamp_limit(limit: int) -> int:
    return min(limit, MAX_LIMIT)


def register(mcp: FastMCP, client_factory: Callable[[], KeapClient | None]) -> None:
    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def keap_list_contacts(
        given_name: Annotated[str | None, Field(description="Filter by first name.")] = None,
        family_name: Annotated[str | None, Field(description="Filter by last name.")] = None,
        email: Annotated[str | None, Field(description="Filter by email address.")] = None,
        limit: Annotated[int, Field(description=_LIMIT_DESC)] = 20,
        offset: Annotated[int, Field(description="Pagination offset.")] = 0,
        order: Annotated[
            str | None,
            Field(description='Sort field: "id", "date_created", "last_updated", "name", or "email".'),
        ] = None,
    ) -> str:
        """List contacts, optionally filtered by name or email."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "given_name": given_name,
            "family_name": family_name,
            "email": email,
            "limit": _clamp_limit(limit),
            "offset": offset,
            "order": order,
        }
        try:
            result = await client.get("/contacts", params=params)
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def keap_get_contact(
        contact_id: Annotated[str, Field(description="The contact's unique ID.")],
        optional_properties: Annotated[
            str | None,
            Field(
                description='Comma-separated extra fields to include, e.g. "custom_fields,job_title,lead_source_id".'
            ),
        ] = None,
    ) -> str:
        """Retrieve a single contact by ID."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                f"/contacts/{contact_id}", params={"optional_properties": optional_properties}
            )
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False))
    async def keap_create_contact(
        given_name: Annotated[str | None, Field(description="First name.")] = None,
        family_name: Annotated[str | None, Field(description="Last name.")] = None,
        email_addresses: Annotated[
            list[dict] | None,
            Field(description='List of dicts, e.g. [{"email": "a@b.com", "field": "EMAIL1"}].'),
        ] = None,
        phone_numbers: Annotated[
            list[dict] | None,
            Field(description='List of dicts, e.g. [{"number": "555-0100", "field": "PHONE1"}].'),
        ] = None,
        addresses: Annotated[
            list[dict] | None,
            Field(
                description=(
                    'List of dicts, e.g. [{"line1": "...", "locality": "...", "region": "...", '
                    '"postal_code": "...", "country_code": "US", "field": "BILLING"}].'
                )
            ),
        ] = None,
        custom_fields: Annotated[
            list[dict] | None,
            Field(description='List of dicts, e.g. [{"id": 1, "content": "value"}].'),
        ] = None,
    ) -> str:
        """Create a contact. Must include at least one email address or phone number."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        body = {
            "given_name": given_name,
            "family_name": family_name,
            "email_addresses": email_addresses,
            "phone_numbers": phone_numbers,
            "addresses": addresses,
            "custom_fields": custom_fields,
        }
        try:
            result = await client.post(
                "/contacts", {k: v for k, v in body.items() if v is not None}
            )
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def keap_list_contact_tags(
        contact_id: Annotated[str, Field(description="The contact's unique ID.")],
        limit: Annotated[int, Field(description=_LIMIT_DESC)] = 20,
        offset: Annotated[int, Field(description="Pagination offset.")] = 0,
    ) -> str:
        """List the tags applied to a contact."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                f"/contacts/{contact_id}/tags",
                params={"limit": _clamp_limit(limit), "offset": offset},
            )
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True))
    async def keap_apply_tags_to_contact(
        contact_id: Annotated[str, Field(description="The contact's unique ID.")],
        tag_ids: Annotated[list[int], Field(description="List of tag IDs to apply.")],
    ) -> str:
        """Apply one or more tags to a contact."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.post(f"/contacts/{contact_id}/tags", {"tagIds": tag_ids})
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def keap_list_tags(
        category: Annotated[int | None, Field(description="Filter by tag category ID.")] = None,
        name: Annotated[str | None, Field(description="Filter by tag name.")] = None,
        limit: Annotated[int, Field(description=_LIMIT_DESC)] = 20,
        offset: Annotated[int, Field(description="Pagination offset.")] = 0,
    ) -> str:
        """List all tags defined in the app."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {"category": category, "name": name, "limit": _clamp_limit(limit), "offset": offset}
        try:
            result = await client.get("/tags", params=params)
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def keap_list_opportunities(
        user_id: Annotated[int | None, Field(description="Filter by the owning user's ID.")] = None,
        stage_id: Annotated[int | None, Field(description="Filter by pipeline stage ID.")] = None,
        search_term: Annotated[str | None, Field(description="Free-text search.")] = None,
        limit: Annotated[int, Field(description=_LIMIT_DESC)] = 20,
        offset: Annotated[int, Field(description="Pagination offset.")] = 0,
        order: Annotated[
            str | None,
            Field(
                description='Sort field: "next_action", "opportunity_name", "contact_name", or "date_created".'
            ),
        ] = None,
    ) -> str:
        """List sales opportunities (deals)."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "user_id": user_id,
            "stage_id": stage_id,
            "search_term": search_term,
            "limit": _clamp_limit(limit),
            "offset": offset,
            "order": order,
        }
        try:
            result = await client.get("/opportunities", params=params)
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def keap_get_opportunity(
        opportunity_id: Annotated[str, Field(description="The opportunity's unique ID.")],
        optional_properties: Annotated[
            str | None, Field(description="Comma-separated list of extra fields to include.")
        ] = None,
    ) -> str:
        """Retrieve a single opportunity by ID."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                f"/opportunities/{opportunity_id}",
                params={"optional_properties": optional_properties},
            )
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False))
    async def keap_create_opportunity(
        contact_id: Annotated[int, Field(description="The contact ID this opportunity is for.")],
        stage_id: Annotated[int, Field(description="The pipeline stage ID to place it in.")],
        opportunity_title: Annotated[str, Field(description="Title of the opportunity.")],
        user_id: Annotated[int | None, Field(description="The owning user's ID.")] = None,
        next_action_date: Annotated[
            str | None, Field(description="ISO 8601 date/time for the next action.")
        ] = None,
        next_action_notes: Annotated[
            str | None, Field(description="Notes for the next action.")
        ] = None,
        opportunity_notes: Annotated[
            str | None, Field(description="General notes on the opportunity.")
        ] = None,
        estimated_close_date: Annotated[
            str | None, Field(description="ISO 8601 date for the estimated close.")
        ] = None,
        projected_revenue_low: Annotated[
            float | None, Field(description="Low end of the projected revenue range.")
        ] = None,
        projected_revenue_high: Annotated[
            float | None, Field(description="High end of the projected revenue range.")
        ] = None,
    ) -> str:
        """Create a sales opportunity (deal)."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        body = {
            "contact": {"id": contact_id},
            "stage": {"id": stage_id},
            "opportunity_title": opportunity_title,
            "user": {"id": user_id} if user_id is not None else None,
            "next_action_date": next_action_date,
            "next_action_notes": next_action_notes,
            "opportunity_notes": opportunity_notes,
            "estimated_close_date": estimated_close_date,
            "projected_revenue_low": projected_revenue_low,
            "projected_revenue_high": projected_revenue_high,
        }
        try:
            result = await client.post(
                "/opportunities", {k: v for k, v in body.items() if v is not None}
            )
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def keap_list_notes(
        contact_id: Annotated[int | None, Field(description="Filter by contact ID.")] = None,
        user_id: Annotated[
            int | None, Field(description="Filter by the note's owning user ID.")
        ] = None,
        limit: Annotated[int, Field(description=_LIMIT_DESC)] = 20,
        offset: Annotated[int, Field(description="Pagination offset.")] = 0,
    ) -> str:
        """List notes."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "contact_id": contact_id,
            "user_id": user_id,
            "limit": _clamp_limit(limit),
            "offset": offset,
        }
        try:
            result = await client.get("/notes", params=params)
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False))
    async def keap_create_note(
        contact_id: Annotated[int, Field(description="The contact this note is attached to.")],
        title: Annotated[str | None, Field(description="Note title.")] = None,
        body: Annotated[str | None, Field(description="Note body text.")] = None,
        type: Annotated[
            str | None,
            Field(description='One of "Appointment", "Call", "Email", "Fax", "Letter", "Other".'),
        ] = None,
        user_id: Annotated[int | None, Field(description="The owning user's ID.")] = None,
    ) -> str:
        """Create a note on a contact. Must include at least a title or body."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        payload = {
            "contact_id": contact_id,
            "title": title,
            "body": body,
            "type": type,
            "user_id": user_id,
        }
        try:
            result = await client.post(
                "/notes", {k: v for k, v in payload.items() if v is not None}
            )
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def keap_list_tasks(
        contact_id: Annotated[int | None, Field(description="Filter by related contact ID.")] = None,
        user_id: Annotated[
            int | None, Field(description="Filter by the assigned user's ID.")
        ] = None,
        completed: Annotated[
            bool | None, Field(description="Filter by completion status.")
        ] = None,
        has_due_date: Annotated[
            bool | None, Field(description="Filter to tasks that have (or don't have) a due date.")
        ] = None,
        limit: Annotated[int, Field(description=_LIMIT_DESC)] = 20,
        offset: Annotated[int, Field(description="Pagination offset.")] = 0,
        order: Annotated[str | None, Field(description="Sort field.")] = None,
    ) -> str:
        """List tasks."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "contact_id": contact_id,
            "user_id": user_id,
            "completed": completed,
            "has_due_date": has_due_date,
            "limit": _clamp_limit(limit),
            "offset": offset,
            "order": order,
        }
        try:
            result = await client.get("/tasks", params=params)
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False))
    async def keap_create_task(
        title: Annotated[str, Field(description="Task title.")],
        due_date: Annotated[str, Field(description="ISO 8601 date/time the task is due.")],
        description: Annotated[str | None, Field(description="Task description.")] = None,
        type: Annotated[str | None, Field(description="Task type/category.")] = None,
        priority: Annotated[str | None, Field(description="Task priority.")] = None,
        contact_id: Annotated[int | None, Field(description="Related contact ID.")] = None,
        user_id: Annotated[int | None, Field(description="Assigned user's ID.")] = None,
        remind_time: Annotated[
            int | None,
            Field(
                description="Minutes before due_date to remind: one of 5/10/15/30/60/120/240/480/1440/2880."
            ),
        ] = None,
    ) -> str:
        """Create a task. Must include at least a title and due date."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        body = {
            "title": title,
            "due_date": due_date,
            "description": description,
            "type": type,
            "priority": priority,
            "contact": {"id": contact_id} if contact_id is not None else None,
            "user_id": user_id,
            "remind_time": remind_time,
        }
        try:
            result = await client.post("/tasks", {k: v for k, v in body.items() if v is not None})
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def keap_list_campaigns(
        search_text: Annotated[
            str | None, Field(description="Free-text search on campaign name.")
        ] = None,
        limit: Annotated[int, Field(description=_LIMIT_DESC)] = 20,
        offset: Annotated[int, Field(description="Pagination offset.")] = 0,
        order: Annotated[
            str | None,
            Field(description='Sort field: "id", "name", "published_date", "status", or "category".'),
        ] = None,
    ) -> str:
        """List marketing/automation campaigns."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "search_text": search_text,
            "limit": _clamp_limit(limit),
            "offset": offset,
            "order": order,
        }
        try:
            result = await client.get("/campaigns", params=params)
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def keap_list_users(
        include_inactive: Annotated[
            bool | None, Field(description="Include inactive users.")
        ] = None,
        include_partners: Annotated[
            bool | None, Field(description="Include partner users.")
        ] = None,
        limit: Annotated[int, Field(description=_LIMIT_DESC)] = 20,
        offset: Annotated[int, Field(description="Pagination offset.")] = 0,
    ) -> str:
        """List users of the Keap app."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "include_inactive": include_inactive,
            "include_partners": include_partners,
            "limit": _clamp_limit(limit),
            "offset": offset,
        }
        try:
            result = await client.get("/users", params=params)
            return dump_json_capped(result)
        except KeapError as e:
            return e.to_envelope()
