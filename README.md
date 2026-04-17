# protoAgent

Template repository for building protoLabs A2A agents on LangGraph.

The purpose of this repo is to keep the boring parts — A2A spec
handling, cost/extension emission, tracing, release pipeline —
stable across every agent in the fleet, so forking an agent is
close to a rewrite of `SOUL.md`, `graph/prompts.py`, and
`tools/lg_tools.py` and not much else.

**Canonical reference implementation**: [protoLabsAI/quinn](https://github.com/protoLabsAI/quinn).
Quinn was the first agent built on this template — it's a good
example of what a filled-in fork looks like end-to-end.

Start a new agent by clicking **"Use this template"** at the top
of the GitHub repo. See [TEMPLATE.md](./TEMPLATE.md) for the
step-by-step fork checklist.

## What you get out of the box

| Concern | Where it lives | What it does |
|---|---|---|
| A2A server | `a2a_handler.py` | JSON-RPC 2.0 over `/a2a`, SSE streaming, `tasks/*` lifecycle, push notifications, well-known agent card, dual token-shape parsing |
| Agent runtime | `graph/agent.py`, `server.py` | LangGraph `create_agent()` wired to the A2A handler, with streaming token capture for cost-v1 |
| LLM gateway | `graph/llm.py` | OpenAI-compatible client pointed at LiteLLM — swap models by editing the gateway config, not the fork |
| Subagents | `graph/subagents/config.py` | DeerFlow-pattern delegation via a `task()` tool; one placeholder `worker` ships |
| Tracing | `tracing.py` | Langfuse trace_session with distributed `a2a.trace` propagation and the OTel cross-context-detach filter |
| Observability | `metrics.py`, `audit.py` | Prometheus metrics with per-agent prefix, JSONL audit log with trace IDs |
| Output protocol | `graph/output_format.py` | `<scratch_pad>` / `<output>` parsing so the model can think without it leaking to users |
| UI | `chat_ui.py`, `static/` | Gradio chat with PWA shell, dark theme, offline fallback |
| Release pipeline | `.github/workflows/*.yml` | Autonomous semver bumps, GHCR image push, GitHub release with filtered notes, optional Discord post |

## Quickstart

```bash
# 1. Click "Use this template" on GitHub, or:
gh repo create protoLabsAI/my-agent \
    --template protoLabsAI/protoAgent \
    --public --clone

cd my-agent

# 2. Rename the agent (one env var, read by server.py, metrics, tracing)
export AGENT_NAME=my-agent

# 3. Boot the container
docker build -t my-agent:local .
docker run --rm -p 7870:7870 -e AGENT_NAME=my-agent my-agent:local

# 4. Hit the agent card
curl http://localhost:7870/.well-known/agent-card.json
```

See [TEMPLATE.md](./TEMPLATE.md) for the full fork checklist.

## Architecture

```
┌──────────────┐     A2A JSON-RPC + SSE      ┌─────────────────┐
│   Consumer   │ ──────────────────────────▶ │  a2a_handler    │
│  (any A2A    │                             │  (FastAPI)      │
│   client)    │ ◀──── cost-v1 DataPart ─────│                 │
└──────────────┘                             └────────┬────────┘
                                                      │
                                                      ▼
                                            ┌─────────────────┐
                                            │  graph/agent.py │
                                            │  (LangGraph     │
                                            │   create_agent) │
                                            └────────┬────────┘
                                                      │
                                                      ▼
                                            ┌─────────────────┐
                                            │  LiteLLM        │  ← model selection
                                            │  gateway        │    lives here,
                                            └─────────────────┘    not in code
```

The A2A handler never talks to the LLM directly — it submits a
message to the LangGraph runtime, which owns the tool loop, the
subagent `task()` delegation, and the structured-output protocol.

## A2A extensions shipped by default

| URI | Declared on card | Emitted at runtime |
|---|---|---|
| `cost-v1` (`https://protolabs.ai/a2a/ext/cost-v1`) | Yes | Yes — every terminal task carries a cost-v1 DataPart with token usage + `durationMs` |
| `a2a.trace` propagation | No (it's a protocol convention, not a card extension) | Yes — reads caller's Langfuse trace context from `params.metadata["a2a.trace"]` and nests this agent's trace under it |

Declare additional extensions on the card in
`server.py::_build_agent_card` when your agent's skills actually
mutate shared state (see `effect-domain-v1` in the Workstacean
docs for when this applies).

## Push notification support

The A2A handler supports both token shapes the spec permits:

```jsonc
// Shape 1 — top-level (what @a2a-js/sdk serialises by default)
{ "url": "https://consumer/callback/abc", "token": "shared-secret" }

// Shape 2 — structured (RFC-8821 AuthenticationInfo)
{
  "url": "https://consumer/callback/abc",
  "authentication": { "schemes": ["Bearer"], "credentials": "shared-secret" }
}
```

Both produce `Authorization: Bearer shared-secret` on outgoing
webhooks. If your fork is getting 401s on callbacks, check which
shape the consumer is sending before changing anything —
`_extract_push_token` in `a2a_handler.py` reads both and the
test suite covers both.

## Observability

| What | Where | How to use |
|---|---|---|
| Prometheus metrics | `/metrics` | Scrape; metric prefix is `AGENT_NAME_*` (sanitised) |
| JSONL audit log | `/sandbox/audit/audit.jsonl` | `jq` for forensic replay; every entry has `trace_id` |
| Langfuse traces | `LANGFUSE_*` env vars | Trace tag is `AGENT_NAME`, so filter by tag to find this agent's runs |
| Container logs | `docker logs <container>` | INFO is the default — `LOG_LEVEL=DEBUG` for more |

## Release pipeline

The included GitHub Actions pipeline is optional but opinionated.

- **On every merge to `main`** → `docker-publish.yml` builds and
  pushes `ghcr.io/protolabsai/<image>:latest` + `sha-<short>`.
  Watchtower (or similar) can poll `latest` for auto-deploy.
- **When a non-release PR merges** → `prepare-release.yml` opens a
  "chore: release vX.Y.Z" bump PR, auto-merges it, and pushes a
  semver tag.
- **When a semver tag lands** → `release.yml` builds and pushes
  the stable semver Docker tags, creates a GitHub release with
  filtered notes, and posts a Discord embed via
  `scripts/post-release-notes.mjs`.

All three workflows gate on `github.repository ==
'protoLabsAI/<name>'` so they no-op on clones that haven't
updated the owner — avoids surprise releases on forks. Update
the repo check in all three files when forking.

## Requirements

- Python 3.12+
- Docker (for the bundled deployment)
- A LiteLLM-compatible OpenAI gateway somewhere on the network
  (see `config/langgraph-config.yaml`)
- Optional: Langfuse, Prometheus, Discord webhook

## Contributing

This is a template repo — bugs and improvements to the shared
runtime (`a2a_handler.py`, `graph/agent.py`, extension support,
release pipeline) land here. Domain-specific agent logic lives
in the fork, not here.
