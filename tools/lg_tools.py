"""LangChain/LangGraph tool adapters for protoAgent.

This is the integration point between the A2A handler and your agent's
business logic. Each ``@tool`` function becomes a LangGraph node that
the lead agent can invoke during a run.

The template ships with a single ``echo`` tool so the handler has
something to wire end-to-end. Replace it with your agent's real tools
(API clients, DB queries, file ops, etc.) and update
``get_all_tools()`` to return the full list.

Every tool that hits an external service should:

- Require explicit identifiers on every call — don't silently fall
  back to env-var defaults for something like ``repo`` / ``project``.
  (An LLM that forgets to pass ``repo`` and picks up a global default
  will fire the call at the wrong target every time.)
- Return clear error strings on failure (the LLM reads them and
  retries) rather than raising — exceptions bubble to the A2A
  handler's ``_deliver_webhook`` path and may surface as 500s.
- Log tool invocations at INFO — ``AuditMiddleware`` already stamps
  duration + success/failure, but domain-specific logs go here.
"""

from langchain_core.tools import tool


@tool
async def echo(message: str) -> str:
    """Echo the input back with a prefix. Template-only sanity tool.

    Replace this with your agent's actual tools. Delete it once your
    real tools are in place — the template ships it so a fresh clone
    can boot, run a skill, and see a roundtrip before you add domain
    logic.
    """
    return f"echo: {message}"


def get_all_tools(knowledge_store=None):
    """Return every LangChain tool the lead agent + subagents can use.

    ``knowledge_store`` is threaded through for agents that ship a
    knowledge / memory subsystem (see ``graph/middleware/knowledge.py``
    for the hook-in pattern). The template doesn't ship a store — the
    parameter is kept so adding one later doesn't require touching
    every call site.
    """
    return [echo]
