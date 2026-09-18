#!/usr/bin/env python3
"""Drives the real user journey against a deployed Octop (source project or
stranger scratch deploy). Usage: python3 live.py <domain> <admin-password>
Exits nonzero on any failure. A green healthcheck alone is NOT proof."""
import json
import sys
import urllib.request

domain, password = sys.argv[1], sys.argv[2]
base = f"https://{domain}" if not domain.startswith("http") else domain
fails = []


def req(method, path, body=None, token=None, expect=(200,)):
    r = urllib.request.Request(base + path, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(urllib.request.Request(base + path, data=data, method=method, headers=dict(r.header_items())), timeout=30) as resp:
            code, payload = resp.status, resp.read()
    except urllib.error.HTTPError as e:
        code, payload = e.code, e.read()
    return code, payload


def check(name, ok, detail=""):
    print(("ok    " if ok else "FAIL  ") + name + (f" ({detail})" if detail and not ok else ""))
    if not ok:
        fails.append(name)


code, _ = req("GET", "/api/health")
check("health endpoint 200", code == 200, f"got {code}")

code, html = req("GET", "/")
check("dashboard HTML served", code == 200 and b"<html" in html.lower(), f"got {code}")

code, body = req("POST", "/api/auth/login", {"username": "admin", "password": password})
token = ""
if code == 200:
    token = json.loads(body).get("access_token", "")
check("admin login works", bool(token), f"got {code}: {body[:200]!r}")

if token:
    code, body = req("GET", "/api/auth/me", token=token)
    check("JWT unlocks profile", code == 200 and b"admin" in body, f"got {code}")

code, _ = req("GET", "/api/auth/me")
check("unauthenticated API rejected", code in (401, 403), f"got {code}")

code, body = req("POST", "/api/auth/login", {"username": "admin", "password": "WrongPass999"})
check("wrong password rejected", code != 200, f"got {code}")

print()
if fails:
    print(f"{len(fails)} FAILED"); sys.exit(1)
print("all passed")
