"""Keap (Infusionsoft) CRM tools: Contacts, Tags, Opportunities, Notes, Tasks, Campaigns, Users.

Tool naming convention: keap_<action>_<resource>
"""

import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import KeapClient, KeapError

_NO_CREDS = (
    "Error: No Keap credentials configured. Set KEAP_ACCESS_TOKEN or use AUTH_MODE=gateway."
)


def register(mcp: FastMCP, client_factory: Callable[[], KeapClient | None]) -> None:
    @mcp.tool()
    async def keap_list_contacts(
        given_name: str | None = None,
        family_name: str | None = None,
        email: str | None = None,
        limit: int = 20,
        offset: int = 0,
        order: str | None = None,
    ) -> str:
        """List contacts.

        API: GET /contacts

        Args:
            given_name: Filter by first name.
            family_name: Filter by last name.
            email: Filter by email address.
            limit: Max results per page (default 20).
            offset: Pagination offset.
            order: Sort field, e.g. "id", "date_created", "last_updated", "name", "email".
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {
            "given_name": given_name,
            "family_name": family_name,
            "email": email,
            "limit": limit,
            "offset": offset,
            "order": order,
        }
        try:
            result = await client.get("/contacts", params=params)
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_get_contact(contact_id: str, optional_properties: str | None = None) -> str:
        """Retrieve a single contact by ID.

        API: GET /contacts/{id}

        Args:
            contact_id: The contact's unique ID.
            optional_properties: Comma-separated list of extra fields to include,
                e.g. "custom_fields,job_title,lead_source_id".
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        try:
            result = await client.get(
                f"/contacts/{contact_id}", params={"optional_properties": optional_properties}
            )
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_create_contact(
        given_name: str | None = None,
        family_name: str | None = None,
        email_addresses: list[dict] | None = None,
        phone_numbers: list[dict] | None = None,
        addresses: list[dict] | None = None,
        custom_fields: list[dict] | None = None,
    ) -> str:
        """Create a contact. Must include at least one email address or phone number.

        API: POST /contacts

        Args:
            given_name: First name.
            family_name: Last name.
            email_addresses: List of dicts, e.g. [{"email": "a@b.com", "field": "EMAIL1"}].
            phone_numbers: List of dicts, e.g. [{"number": "555-0100", "field": "PHONE1"}].
            addresses: List of dicts, e.g. [{"line1": "...", "locality": "...", "region": "...",
                "postal_code": "...", "country_code": "US", "field": "BILLING"}].
            custom_fields: List of dicts, e.g. [{"id": 1, "content": "value"}].
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        body = {
            "given_name": given_name,
            "family_name": family_name,
            "email_addresses": email_addresses,
            "phone_numbers": phone_numbers,
            "addresses": addresses,
            "custom_fields": custom_fields,
        }
        try:
            result = await client.post("/contacts", {k: v for k, v in body.items() if v is not None})
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_list_contact_tags(contact_id: str, limit: int = 20, offset: int = 0) -> str:
        """List the tags applied to a contact.

        API: GET /contacts/{contactId}/tags

        Args:
            contact_id: The contact's unique ID.
            limit: Max results per page.
            offset: Pagination offset.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        try:
            result = await client.get(
                f"/contacts/{contact_id}/tags", params={"limit": limit, "offset": offset}
            )
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_apply_tags_to_contact(contact_id: str, tag_ids: list[int]) -> str:
        """Apply one or more tags to a contact.

        API: POST /contacts/{contactId}/tags

        Args:
            contact_id: The contact's unique ID.
            tag_ids: Required. List of tag IDs to apply.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        try:
            result = await client.post(f"/contacts/{contact_id}/tags", {"tagIds": tag_ids})
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_list_tags(
        category: int | None = None,
        name: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> str:
        """List all tags defined in the app.

        API: GET /tags

        Args:
            category: Filter by tag category ID.
            name: Filter by tag name.
            limit: Max results per page.
            offset: Pagination offset.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {"category": category, "name": name, "limit": limit, "offset": offset}
        try:
            result = await client.get("/tags", params=params)
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_list_opportunities(
        user_id: int | None = None,
        stage_id: int | None = None,
        search_term: str | None = None,
        limit: int = 20,
        offset: int = 0,
        order: str | None = None,
    ) -> str:
        """List sales opportunities (deals).

        API: GET /opportunities

        Args:
            user_id: Filter by the owning user's ID.
            stage_id: Filter by pipeline stage ID.
            search_term: Free-text search.
            limit: Max results per page.
            offset: Pagination offset.
            order: Sort field, e.g. "next_action", "opportunity_name", "contact_name", "date_created".
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {
            "user_id": user_id,
            "stage_id": stage_id,
            "search_term": search_term,
            "limit": limit,
            "offset": offset,
            "order": order,
        }
        try:
            result = await client.get("/opportunities", params=params)
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_get_opportunity(opportunity_id: str, optional_properties: str | None = None) -> str:
        """Retrieve a single opportunity by ID.

        API: GET /opportunities/{opportunityId}

        Args:
            opportunity_id: The opportunity's unique ID.
            optional_properties: Comma-separated list of extra fields to include.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        try:
            result = await client.get(
                f"/opportunities/{opportunity_id}", params={"optional_properties": optional_properties}
            )
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_create_opportunity(
        contact_id: int,
        stage_id: int,
        opportunity_title: str,
        user_id: int | None = None,
        next_action_date: str | None = None,
        next_action_notes: str | None = None,
        opportunity_notes: str | None = None,
        estimated_close_date: str | None = None,
        projected_revenue_low: float | None = None,
        projected_revenue_high: float | None = None,
    ) -> str:
        """Create a sales opportunity (deal).

        API: POST /opportunities

        Args:
            contact_id: Required. The contact ID this opportunity is for.
            stage_id: Required. The pipeline stage ID to place it in.
            opportunity_title: Required. Title of the opportunity.
            user_id: The owning user's ID.
            next_action_date: ISO 8601 date/time for the next action.
            next_action_notes: Notes for the next action.
            opportunity_notes: General notes on the opportunity.
            estimated_close_date: ISO 8601 date for the estimated close.
            projected_revenue_low: Low end of the projected revenue range.
            projected_revenue_high: High end of the projected revenue range.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
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
            result = await client.post("/opportunities", {k: v for k, v in body.items() if v is not None})
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_list_notes(
        contact_id: int | None = None,
        user_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> str:
        """List notes.

        API: GET /notes

        Args:
            contact_id: Filter by contact ID.
            user_id: Filter by the note's owning user ID.
            limit: Max results per page.
            offset: Pagination offset.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {"contact_id": contact_id, "user_id": user_id, "limit": limit, "offset": offset}
        try:
            result = await client.get("/notes", params=params)
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_create_note(
        contact_id: int,
        title: str | None = None,
        body: str | None = None,
        type: str | None = None,
        user_id: int | None = None,
    ) -> str:
        """Create a note on a contact. Must include at least a title or body.

        API: POST /notes

        Args:
            contact_id: Required. The contact this note is attached to.
            title: Note title.
            body: Note body text.
            type: One of "Appointment", "Call", "Email", "Fax", "Letter", "Other".
            user_id: The owning user's ID.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        payload = {
            "contact_id": contact_id,
            "title": title,
            "body": body,
            "type": type,
            "user_id": user_id,
        }
        try:
            result = await client.post("/notes", {k: v for k, v in payload.items() if v is not None})
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_list_tasks(
        contact_id: int | None = None,
        user_id: int | None = None,
        completed: bool | None = None,
        has_due_date: bool | None = None,
        limit: int = 20,
        offset: int = 0,
        order: str | None = None,
    ) -> str:
        """List tasks.

        API: GET /tasks

        Args:
            contact_id: Filter by related contact ID.
            user_id: Filter by the assigned user's ID.
            completed: Filter by completion status.
            has_due_date: Filter to tasks that have (or don't have) a due date.
            limit: Max results per page.
            offset: Pagination offset.
            order: Sort field.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {
            "contact_id": contact_id,
            "user_id": user_id,
            "completed": completed,
            "has_due_date": has_due_date,
            "limit": limit,
            "offset": offset,
            "order": order,
        }
        try:
            result = await client.get("/tasks", params=params)
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_create_task(
        title: str,
        due_date: str,
        description: str | None = None,
        type: str | None = None,
        priority: str | None = None,
        contact_id: int | None = None,
        user_id: int | None = None,
        remind_time: int | None = None,
    ) -> str:
        """Create a task. Must include at least a title and due date.

        API: POST /tasks

        Args:
            title: Required. Task title.
            due_date: Required. ISO 8601 date/time the task is due.
            description: Task description.
            type: Task type/category.
            priority: Task priority.
            contact_id: Related contact ID.
            user_id: Assigned user's ID.
            remind_time: Minutes before due_date to remind, one of
                5/10/15/30/60/120/240/480/1440/2880.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
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
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_list_campaigns(
        search_text: str | None = None,
        limit: int = 20,
        offset: int = 0,
        order: str | None = None,
    ) -> str:
        """List marketing/automation campaigns.

        API: GET /campaigns

        Args:
            search_text: Free-text search on campaign name.
            limit: Max results per page.
            offset: Pagination offset.
            order: Sort field, e.g. "id", "name", "published_date", "status", "category".
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {"search_text": search_text, "limit": limit, "offset": offset, "order": order}
        try:
            result = await client.get("/campaigns", params=params)
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def keap_list_users(
        include_inactive: bool | None = None,
        include_partners: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> str:
        """List users of the Keap app.

        API: GET /users

        Args:
            include_inactive: Include inactive users.
            include_partners: Include partner users.
            limit: Max results per page.
            offset: Pagination offset.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {
            "include_inactive": include_inactive,
            "include_partners": include_partners,
            "limit": limit,
            "offset": offset,
        }
        try:
            result = await client.get("/users", params=params)
            return json.dumps(result, indent=2)
        except KeapError as e:
            return f"Error: {e}"
