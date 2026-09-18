#!/usr/bin/env bash
# Contract tests for ghcr.io/hmseeb/octop-railway. Written red, run against the
# pushed image. Boots the real first-run path (entrypoint init, admin creation)
# and drives the actual login journey over HTTP.
set -uo pipefail
cd "$(dirname "$0")"

PASSWORD="${CONTRACT_PASSWORD:-ContractPass123}"
export CONTRACT_PASSWORD="$PASSWORD"
BASE="http://localhost:8088"
COMPOSE="docker compose -f compose.yml -p octop-contract"
pass=0; fail=0

check() { # name, condition-already-evaluated (0/1)
  if [ "$2" -eq 0 ]; then echo "ok    $1"; pass=$((pass+1)); else echo "FAIL  $1"; fail=$((fail+1)); fi
}

wait_for() { # url, timeout_secs
  local url="$1" n="${2:-240}" i
  for ((i=0; i<n; i++)); do
    curl -sf -o /dev/null "$url" && return 0
    sleep 1
  done
  return 1
}

$COMPOSE down -v >/dev/null 2>&1 || true
echo "== booting (first-run init creates the admin) =="
$COMPOSE up -d >/dev/null 2>&1 || { echo "compose up failed"; $COMPOSE logs --tail 40; exit 1; }

wait_for "$BASE/api/health" 300
check "health endpoint answers" $?

out=$(curl -s "$BASE/")
echo "$out" | grep -qi "<html" ; check "dashboard HTML served at /" $?

# Real login journey: password from env -> JWT -> authenticated profile.
token=$(curl -s -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"username\":\"admin\",\"password\":\"$PASSWORD\"}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("access_token",""))' 2>/dev/null)
[ -n "$token" ]; check "admin can log in with the env password" $?

me=$(curl -s "$BASE/api/auth/me" -H "Authorization: Bearer $token")
echo "$me" | grep -q '"admin"'; check "JWT unlocks /api/auth/me as admin" $?

code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/auth/me")
[ "$code" = "401" ] || [ "$code" = "403" ]; check "unauthenticated API is rejected ($code)" $?

# Railway needs the listener on BOTH stacks: private network dials IPv6, the
# health checker speaks IPv4.
docker exec octop-contract-octop-1 sh -c 'curl -sf -o /dev/null http://[::1]:8088/api/health' 2>/dev/null
check "answers on IPv6 loopback" $?
docker exec octop-contract-octop-1 sh -c 'curl -sf -o /dev/null http://127.0.0.1:8088/api/health' 2>/dev/null
check "answers on IPv4 loopback (dual-stack socket)" $?

# Wrong password must not mint a token (login is not a formality).
code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' -d '{"username":"admin","password":"WrongPass999"}')
[ "$code" != "200" ]; check "wrong password rejected ($code)" $?

echo
echo "$pass passed, $fail failed"
$COMPOSE down -v >/dev/null 2>&1
[ "$fail" -eq 0 ]
