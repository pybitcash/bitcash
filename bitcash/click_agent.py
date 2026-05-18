"""
click_agent.py — lightweight @agent decorator for Click CLIs.

Attaches agent-readable metadata to Click commands and groups.
Vocabulary borrowed from MCP ToolAnnotations (2025-03-26 spec), extended
with `secret` and `local_required` (Microsoft azmcp) and `blocking` (new).

Absent fields are omitted from schema output — agents should treat an
absent field as unknown, not as a safe default.
"""

from __future__ import annotations

import json
from typing import Any

import click  # pyright: ignore

_AGENT_FIELDS = {
    "read_only",
    "destructive",
    "idempotent",
    "open_world",
    "secret",
    "local_required",
    "blocking",
    "skill",
}


def agent(**kwargs: Any):
    """Attach agent-readable metadata to a Click command or group.

    All fields are optional. Unset fields are omitted from schema output.

    Fields (MCP-compatible unless noted):
      read_only      — no state is modified anywhere
      destructive    — modification is irreversible (only when read_only=False)
      idempotent     — repeating with same args has no additional effect
      open_world     — makes network calls / reaches external systems
      secret         — output may contain sensitive data; do not log
      local_required — requires local state (wallet store, config files) [azmcp]
      blocking       — blocks indefinitely until externally interrupted [new]
      skill          — URL to a SKILL.md document for workflow-level context [new]
    """
    unknown = set(kwargs) - _AGENT_FIELDS
    if unknown:
        raise ValueError(f"Unknown @agent fields: {unknown}")

    def decorator(f: Any) -> Any:
        f.__agent_meta__ = kwargs
        return f

    return decorator


def _safe_default(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return None


def _serialize_command(cmd: click.BaseCommand) -> dict:
    node: dict = {}

    if cmd.help:
        node["help"] = cmd.help

    meta = getattr(cmd.callback, "__agent_meta__", {})
    if meta:
        node["agent"] = meta

    if isinstance(cmd, click.Group):
        node["commands"] = {
            name: _serialize_command(sub) for name, sub in cmd.commands.items()
        }
    else:
        params = []
        for p in cmd.params:
            if p.name == "help":
                continue
            if isinstance(p, click.Argument):
                params.append(
                    {"name": p.name, "kind": "argument", "required": p.required}
                )
            elif isinstance(p, click.Option):
                entry: dict = {
                    "name": p.name,
                    "kind": "option",
                    "required": p.required,
                    "flags": list(p.opts),
                    "help": p.help or "",
                    "default": _safe_default(p.default),
                }
                if p.is_flag:
                    entry["is_flag"] = True
                if isinstance(p.type, click.Choice):
                    entry["choices"] = list(p.type.choices)
                params.append(entry)
        if params:
            node["params"] = params

    return node


def add_schema_command(group: click.Group) -> None:
    """Inject a 'schema' subcommand into a Click group.

    Call this after all commands have been registered on the group.
    """

    @group.command(name="schema")
    @click.pass_context
    def schema_cmd(ctx: click.Context) -> None:
        """Emit the full command tree as JSON for agent consumption.

        Includes help text, agent metadata (read_only, destructive,
        idempotent, open_world, secret, local_required, blocking, skill),
        parameter names, kinds, flags, defaults, and choices. No network calls.
        """
        root = ctx.find_root()
        click.echo(json.dumps(_serialize_command(root.command), indent=2))
