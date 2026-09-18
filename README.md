# Octop Railway Template

One-click Railway template for [Octop](https://github.com/TencentCloud/Octop),
a self-hosted multi-user AI assistant: web dashboard, IM channels, cron
automation, and per-user agent teams in one process.

<!-- Deploy button URL goes here after publish -->

## What this repo is

- `.github/workflows/build.yml` — builds upstream `docker/Dockerfile` at tag
  `v1.0.0` and pushes `ghcr.io/hmseeb/octop-railway:1.0.0-r1`, with one patch:
  the stock entrypoint hardcodes `--host 0.0.0.0`, which overrides
  `OCTOP_BIND_HOST` and is unreachable on Railway's IPv6 private network; the
  patch makes the flag honor the env (default `::`).
- `template.json` — the build sheet: topology, variables, and why each choice
  was made.
- `build_source.py` — creates the live source project in the Auromations
  workspace.
- `repair.py` — restores the variable config that `templateGenerate` strips.
- `deploy_as_stranger.py` — click-deploys the template into a fresh project.
- `live.py` — drives the real user journey against a deployment.
- `publish.py` — publishes the listing (asks first; the slug is permanent).
- `test/contract.sh` — boots the exact image + volume shape and checks boot,
  login, JWT auth, and dual-stack listening.

## Layout on Railway

One service (`octop`), one volume at `/data/.octop` (SQLite control-plane DB,
agent workspaces, credential.txt), public domain targeting port 8088.

First boot runs `octop init`: admin user `admin` with the generated
`OCTOP_DEFAULT_PASSWORD` from the variables tab.
