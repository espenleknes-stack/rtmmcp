from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import Settings
from .rtm_api import RTMClient


settings = Settings.load()
client = RTMClient(settings)
mcp = FastMCP("remember-the-milk")


@mcp.tool()
def rtm_auth_begin(perms: str = "delete") -> dict[str, Any]:
    """Start the Remember The Milk auth flow and return the browser approval URL."""
    if perms not in {"read", "write", "delete"}:
        raise ValueError("perms must be one of: read, write, delete")
    return client.start_auth(perms=perms)


@mcp.tool()
def rtm_auth_complete(frob: str | None = None) -> dict[str, Any]:
    """Exchange a frob for a permanent auth token and store it locally."""
    return client.finish_auth(frob=frob)


@mcp.tool()
def rtm_auth_status() -> dict[str, Any]:
    """Report whether a valid RTM auth token is available."""
    return client.auth_status()


@mcp.tool()
def rtm_list_lists() -> list[dict[str, Any]]:
    """Return the user's Remember The Milk lists."""
    return client.get_lists()


@mcp.tool()
def rtm_list_tasks(list_id: str | None = None, filter_text: str | None = None) -> list[dict[str, Any]]:
    """Return tasks, optionally scoped to a list or RTM filter string."""
    return client.get_tasks(list_id=list_id, filter_text=filter_text)


@mcp.tool()
def rtm_add_task(name: str, list_id: str | None = None, parse: bool = True) -> dict[str, Any]:
    """Create a task, optionally in a specific list."""
    return client.add_task(name=name, list_id=list_id, parse=parse)


@mcp.tool()
def rtm_complete_task(list_id: str, taskseries_id: str, task_id: str) -> dict[str, Any]:
    """Complete a specific task instance."""
    return client.complete_task(list_id=list_id, taskseries_id=taskseries_id, task_id=task_id)


@mcp.tool()
def rtm_create_list(name: str, filter_text: str | None = None) -> dict[str, Any]:
    """Create a new Remember The Milk list."""
    return client.create_list(name=name, filter_text=filter_text)


@mcp.tool()
def rtm_archive_list(list_id: str) -> dict[str, Any]:
    """Archive a list."""
    return client.update_list("rtm.lists.archive", list_id=list_id)


@mcp.tool()
def rtm_unarchive_list(list_id: str) -> dict[str, Any]:
    """Unarchive a list."""
    return client.update_list("rtm.lists.unarchive", list_id=list_id)


@mcp.tool()
def rtm_delete_list(list_id: str) -> dict[str, Any]:
    """Delete a list."""
    return client.update_list("rtm.lists.delete", list_id=list_id)


@mcp.tool()
def rtm_rename_list(list_id: str, name: str) -> dict[str, Any]:
    """Rename a list."""
    return client.update_list("rtm.lists.setName", list_id=list_id, name=name)


@mcp.tool()
def rtm_set_default_list(list_id: str) -> dict[str, Any]:
    """Set the default list."""
    return client.update_list("rtm.lists.setDefaultList", list_id=list_id)


@mcp.tool()
def rtm_raw_call(method: str, params: dict[str, Any] | None = None, require_auth: bool = True) -> dict[str, Any]:
    """Call any RTM API method directly."""
    return client.call_method(method, params=params, require_auth=require_auth)


@mcp.tool()
def rtm_delete_task(list_id: str, taskseries_id: str, task_id: str) -> dict[str, Any]:
    """Delete a task."""
    return client.task_method("rtm.tasks.delete", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id)


@mcp.tool()
def rtm_uncomplete_task(list_id: str, taskseries_id: str, task_id: str) -> dict[str, Any]:
    """Mark a task incomplete again."""
    return client.task_method("rtm.tasks.uncomplete", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id)


@mcp.tool()
def rtm_postpone_task(list_id: str, taskseries_id: str, task_id: str) -> dict[str, Any]:
    """Postpone a task."""
    return client.task_method("rtm.tasks.postpone", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id)


@mcp.tool()
def rtm_move_task(
    list_id: str,
    taskseries_id: str,
    task_id: str,
    to_list_id: str,
    direction: str | None = None,
) -> dict[str, Any]:
    """Move a task to another list, optionally with a priority direction."""
    extra: dict[str, Any] = {"to_list_id": to_list_id}
    if direction:
        extra["direction"] = direction
    return client.task_method("rtm.tasks.moveTo", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, extra_params=extra)


@mcp.tool()
def rtm_set_task_name(list_id: str, taskseries_id: str, task_id: str, name: str) -> dict[str, Any]:
    """Rename a task."""
    return client.task_method(
        "rtm.tasks.setName",
        list_id=list_id,
        taskseries_id=taskseries_id,
        task_id=task_id,
        extra_params={"name": name},
    )


@mcp.tool()
def rtm_set_task_priority(list_id: str, taskseries_id: str, task_id: str, priority: str) -> dict[str, Any]:
    """Set a task priority. Use N, 1, 2, or 3."""
    return client.task_method(
        "rtm.tasks.setPriority",
        list_id=list_id,
        taskseries_id=taskseries_id,
        task_id=task_id,
        extra_params={"priority": priority},
    )


@mcp.tool()
def rtm_move_task_priority(list_id: str, taskseries_id: str, task_id: str, direction: str) -> dict[str, Any]:
    """Move a task priority up or down."""
    return client.task_method(
        "rtm.tasks.movePriority",
        list_id=list_id,
        taskseries_id=taskseries_id,
        task_id=task_id,
        extra_params={"direction": direction},
    )


@mcp.tool()
def rtm_set_task_due_date(
    list_id: str,
    taskseries_id: str,
    task_id: str,
    due: str | None = None,
    has_due_time: bool | None = None,
    parse: bool = True,
) -> dict[str, Any]:
    """Set or clear a task due date. Omit due to clear it."""
    extra: dict[str, Any] = {"parse": parse}
    if due is not None:
        extra["due"] = due
    if has_due_time is not None:
        extra["has_due_time"] = has_due_time
    return client.task_method("rtm.tasks.setDueDate", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, extra_params=extra)


@mcp.tool()
def rtm_set_task_start_date(
    list_id: str,
    taskseries_id: str,
    task_id: str,
    start: str | None = None,
    has_start_time: bool | None = None,
    parse: bool = True,
) -> dict[str, Any]:
    """Set or clear a task start date. Omit start to clear it."""
    extra: dict[str, Any] = {"parse": parse}
    if start is not None:
        extra["start"] = start
    if has_start_time is not None:
        extra["has_start_time"] = has_start_time
    return client.task_method("rtm.tasks.setStartDate", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, extra_params=extra)


@mcp.tool()
def rtm_set_task_estimate(list_id: str, taskseries_id: str, task_id: str, estimate: str | None = None) -> dict[str, Any]:
    """Set or clear a task estimate."""
    extra: dict[str, Any] = {}
    if estimate is not None:
        extra["estimate"] = estimate
    return client.task_method("rtm.tasks.setEstimate", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, extra_params=extra)


@mcp.tool()
def rtm_set_task_recurrence(list_id: str, taskseries_id: str, task_id: str, repeat: str | None = None) -> dict[str, Any]:
    """Set or clear a task recurrence rule."""
    extra: dict[str, Any] = {}
    if repeat is not None:
        extra["repeat"] = repeat
    return client.task_method("rtm.tasks.setRecurrence", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, extra_params=extra)


@mcp.tool()
def rtm_set_task_url(list_id: str, taskseries_id: str, task_id: str, url: str | None = None) -> dict[str, Any]:
    """Set or clear a task URL."""
    extra: dict[str, Any] = {}
    if url is not None:
        extra["url"] = url
    return client.task_method("rtm.tasks.setURL", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, extra_params=extra)


@mcp.tool()
def rtm_set_task_location(list_id: str, taskseries_id: str, task_id: str, location_id: str | None = None) -> dict[str, Any]:
    """Set or clear a task location."""
    extra: dict[str, Any] = {}
    if location_id is not None:
        extra["location_id"] = location_id
    return client.task_method("rtm.tasks.setLocation", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, extra_params=extra)


@mcp.tool()
def rtm_set_task_tags(list_id: str, taskseries_id: str, task_id: str, tags: str | list[str] | None = None) -> dict[str, Any]:
    """Replace all tags on a task. Pass a comma-separated string or list of tag names."""
    tag_text = ",".join(tags) if isinstance(tags, list) else tags
    extra: dict[str, Any] = {}
    if tag_text is not None:
        extra["tags"] = tag_text
    return client.task_method("rtm.tasks.setTags", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, extra_params=extra)


@mcp.tool()
def rtm_add_task_tags(list_id: str, taskseries_id: str, task_id: str, tags: str | list[str]) -> dict[str, Any]:
    """Add tags to a task."""
    tag_text = ",".join(tags) if isinstance(tags, list) else tags
    return client.task_method("rtm.tasks.addTags", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, extra_params={"tags": tag_text})


@mcp.tool()
def rtm_remove_task_tags(list_id: str, taskseries_id: str, task_id: str, tags: str | list[str]) -> dict[str, Any]:
    """Remove tags from a task."""
    tag_text = ",".join(tags) if isinstance(tags, list) else tags
    return client.task_method("rtm.tasks.removeTags", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, extra_params={"tags": tag_text})


@mcp.tool()
def rtm_set_parent_task(
    list_id: str,
    taskseries_id: str,
    task_id: str,
    parent_task_id: str | None = None,
) -> dict[str, Any]:
    """Set or clear the parent task for a task."""
    extra: dict[str, Any] = {}
    if parent_task_id is not None:
        extra["parent_task_id"] = parent_task_id
    return client.task_method("rtm.tasks.setParentTask", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, extra_params=extra)


@mcp.tool()
def rtm_add_note(list_id: str, taskseries_id: str, task_id: str, title: str, note_text: str) -> dict[str, Any]:
    """Add a note to a task."""
    return client.note_method("rtm.tasks.notes.add", list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, title=title, note_text=note_text)


@mcp.tool()
def rtm_edit_note(
    note_id: str,
    list_id: str,
    taskseries_id: str,
    task_id: str,
    title: str,
    note_text: str,
) -> dict[str, Any]:
    """Edit a note on a task."""
    return client.note_method("rtm.tasks.notes.edit", note_id=note_id, list_id=list_id, taskseries_id=taskseries_id, task_id=task_id, title=title, note_text=note_text)


@mcp.tool()
def rtm_delete_note(note_id: str, list_id: str, taskseries_id: str, task_id: str) -> dict[str, Any]:
    """Delete a note from a task."""
    return client.note_method("rtm.tasks.notes.delete", note_id=note_id, list_id=list_id, taskseries_id=taskseries_id, task_id=task_id)


@mcp.tool()
def rtm_list_tags() -> list[dict[str, Any]]:
    """Return all tags."""
    return client.call_method("rtm.tags.getList", require_auth=True).get("tags", {}).get("tag", [])


@mcp.tool()
def rtm_list_locations() -> list[dict[str, Any]]:
    """Return all saved locations."""
    return client.call_method("rtm.locations.getList", require_auth=True).get("locations", {}).get("location", [])


@mcp.tool()
def rtm_list_timezones() -> list[dict[str, Any]]:
    """Return available timezones."""
    return client.call_method("rtm.timezones.getList", require_auth=True).get("timezones", {}).get("timezone", [])


@mcp.tool()
def rtm_get_settings() -> dict[str, Any]:
    """Return RTM account settings."""
    return client.call_method("rtm.settings.getList", require_auth=True)


@mcp.tool()
def rtm_list_contacts() -> list[dict[str, Any]]:
    """Return contacts."""
    return client.call_method("rtm.contacts.getList", require_auth=True).get("contacts", {}).get("contact", [])


@mcp.tool()
def rtm_add_contact(timeline: bool, contact: str) -> dict[str, Any]:
    """Add a contact by username or email."""
    return client.contact_method("rtm.contacts.add", timeline=timeline, contact=contact)


@mcp.tool()
def rtm_delete_contact(timeline: bool, contact_id: str) -> dict[str, Any]:
    """Delete a contact."""
    return client.contact_method("rtm.contacts.delete", timeline=timeline, contact_id=contact_id)


@mcp.tool()
def rtm_list_groups() -> list[dict[str, Any]]:
    """Return groups."""
    return client.call_method("rtm.groups.getList", require_auth=True).get("groups", {}).get("group", [])


@mcp.tool()
def rtm_add_group(name: str) -> dict[str, Any]:
    """Create a group."""
    return client.group_method("rtm.groups.add", name=name)


@mcp.tool()
def rtm_delete_group(group_id: str) -> dict[str, Any]:
    """Delete a group."""
    return client.group_method("rtm.groups.delete", group_id=group_id)


@mcp.tool()
def rtm_add_group_contact(group_id: str, contact_id: str) -> dict[str, Any]:
    """Add a contact to a group."""
    return client.group_method("rtm.groups.addContact", group_id=group_id, contact_id=contact_id)


@mcp.tool()
def rtm_remove_group_contact(group_id: str, contact_id: str) -> dict[str, Any]:
    """Remove a contact from a group."""
    return client.group_method("rtm.groups.removeContact", group_id=group_id, contact_id=contact_id)


@mcp.tool()
def rtm_time_parse(text: str, timezone: str | None = None, date_format: str | None = None) -> dict[str, Any]:
    """Parse natural language time text via RTM."""
    params: dict[str, Any] = {"text": text}
    if timezone:
        params["timezone"] = timezone
    if date_format:
        params["dateformat"] = date_format
    return client.call_method("rtm.time.parse", params=params, require_auth=True)


@mcp.tool()
def rtm_time_convert(from_timezone: str, to_timezone: str, time_value: str) -> dict[str, Any]:
    """Convert a time value between timezones."""
    return client.call_method(
        "rtm.time.convert",
        params={"from_timezone": from_timezone, "to_timezone": to_timezone, "time": time_value},
        require_auth=True,
    )


@mcp.tool()
def rtm_undo_transaction(transaction_id: str) -> dict[str, Any]:
    """Undo a revertable transaction."""
    return client.timeline_method("rtm.transactions.undo", {"transaction_id": transaction_id})


@mcp.tool()
def rtm_list_methods() -> list[str]:
    """Return the list of RTM API methods."""
    methods = client.call_method("rtm.reflection.getMethods", require_auth=True).get("methods", {}).get("method", [])
    return methods if isinstance(methods, list) else [methods]


@mcp.tool()
def rtm_get_method_info(method_name: str) -> dict[str, Any]:
    """Return official metadata for an RTM API method."""
    return client.call_method("rtm.reflection.getMethodInfo", params={"method_name": method_name}, require_auth=True)


@mcp.tool()
def rtm_test_echo(params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Echo parameters through the RTM test endpoint."""
    return client.call_method("rtm.test.echo", params=params or {}, require_auth=True)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
