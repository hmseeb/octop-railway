# Deploy and Host Octop on Railway

Octop is a self-hosted, multi-user AI assistant platform. One process serves a
web dashboard, a CLI, IM channels (Feishu, DingTalk, QQ, Discord, WeCom), and
cron automation, all sharing one control-plane database. Each user gets a team
of specialized agents with their own workspaces, providers, and schedules.

## About Hosting Octop

Octop is designed as a single, restart-safe process: FastAPI + uvicorn serving
the API and React dashboard, an agent runtime, a scheduler, and channel bridges,
with state rebuilt from the database on every boot. The default database is
SQLite on a mounted volume, so the whole deployment is one service plus one
volume. PostgreSQL is supported upstream but not required.

On Railway, the volume holds the database, agent workspaces, uploads, and the
credential file, so redeploys keep every conversation and setting.

## Common Use Cases

- Personal AI assistant with persistent memory, reachable from the web dashboard
  and from IM channels like Discord or DingTalk.
- A shared assistant for a household or small team: one admin, multiple users,
  each with their own agents and experts.
- Scheduled automation: natural-language cron jobs that push results to chat on
  a schedule.
- Browser automation and remote desktop sessions driven by agents.
- Delegating coding tasks to external agents over ACP (OpenCode, Claude Code,
  Codex).

## Dependencies for Octop Hosting

### Deployment Dependencies

- One Railway service running the Octop image (built from upstream v1.0.0, see
  Implementation Details).
- One volume mounted at `/data/.octop` for the database and workspaces.
- An LLM provider key (OpenAI-compatible) to make agents answer; it can be set
  as `OPENAI_API_KEY` at deploy time or added later in the dashboard.

### Implementation Details

First boot runs the setup wizard automatically: it creates the admin account
(`OCTOP_ADMIN_USERNAME`, default `admin`) with the generated
`OCTOP_DEFAULT_PASSWORD` shown in the service variables. Open your service
domain, log in, and change the password afterwards. If the password variable is
ever cleared, a random password is generated and written to `credential.txt` on
the volume instead.

Configuration:

- `OCTOP_DEFAULT_PASSWORD` — first-boot admin password (auto-generated per
  deploy). Only consumed on the very first boot; later changes happen in the
  dashboard.
- `OCTOP_ADMIN_USERNAME` — first-boot admin username (default `admin`).
- `OPENAI_API_KEY` — optional; providers are fully manageable in the dashboard.

Upgrading: bump the image tag to a newer `ghcr.io/hmseeb/octop-railway` release
and redeploy. Data lives on the volume and migrations run on boot.

Scaling: Octop is a single-process design with local SQLite by default; run one
replica. For heavier use, upstream supports PostgreSQL as the control-plane
database.

## Why Deploy Octop on Railway?

Railway gives the single-container shape Octop wants: one service, one volume,
a public domain, and zero orchestration. First boot finishes in about a minute,
and the whole assistant, dashboard included, is behind your Railway domain with
TLS handled at the edge.
