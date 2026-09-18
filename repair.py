#!/usr/bin/env python3
"""Puts back everything templateGenerate strips (every literal variable value),
via templateUpsertConfig on the internal endpoint. What templateGenerate hands
back cannot be edited ("Not Authorized"), so generation is a read: its config is
copied into a fresh template with fresh UUIDs everywhere. Pass `new` as the id
the first time and the id it prints thereafter.
Usage: repair.py <templateId|new> <path-to-generated.json>
"""
import json
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path("~/.claude/skills/create-template-for-railway/scripts").expanduser()))
import rw  # noqa: E402

WORKSPACE = "fc4796db-2c6c-4354-a564-d4a1d900af53"  # Auromations
NAME = "Octop"
ICON = "https://raw.githubusercontent.com/hmseeb/octop-railway/ea78288db80ac804a11a543847064d0ce96a0e86/assets/octop-icon.svg"  # square mark from upstream wordmark

# Password policy is >=8 chars with letters and digits; the explicit alphabet
# keeps the generator alphanumeric. If it were ever rejected, the entrypoint
# falls back to a random password written to credential.txt on the volume.
PW_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
PW = '${{ secret(32, "' + PW_ALPHABET + '") }}'


def var(default=None, optional=False, description=None):
    v = {"isOptional": optional}
    if default is not None:
        v["defaultValue"] = default
    if description:
        v["description"] = description
    return v


VARIABLES = {
    "octop": {
        "HOME": var("/data"),
        # Railway injects PORT=8080 on image services; pin it to the app's port
        # so the injected var, OCTOP_PORT and the domain target port all agree.
        "PORT": var("8088"),
        "OCTOP_PORT": var("8088"),
        # IPv6 wildcard for Railway's private network; our image build patches
        # the entrypoint to honor this (stock image hardcodes 0.0.0.0).
        "OCTOP_BIND_HOST": var("::"),
        "OCTOP_ADMIN_USERNAME": var("admin", description="Username of the admin account created on first boot."),
        "OCTOP_DEFAULT_PASSWORD": var(PW, description="Password of the admin account created on first boot. Change it after logging in."),
        "OPENAI_API_KEY": var(optional=True, description="Optional. Any OpenAI-compatible key gets you chatting; more providers can be added in the dashboard."),
    },
}


def main():
    template_id = sys.argv[1]
    config = json.loads(pathlib.Path(sys.argv[2]).read_text())
    if "templateGenerate" in config:
        config = config["templateGenerate"]["serializedConfig"]
    if template_id == "new":
        template_id = str(uuid.uuid4())
        remap = {sid: str(uuid.uuid4()) for sid in config["services"]}
        rebuilt = {"buckets": config.get("buckets", {}), "services": {}}
        for sid, svc in config["services"].items():
            svc = json.loads(json.dumps(svc))
            if "volumeMounts" in svc:
                svc["volumeMounts"] = {remap[k]: v for k, v in svc["volumeMounts"].items()}
            rebuilt["services"][remap[sid]] = svc
        config = rebuilt
        print("minting template", template_id)

    for service in config["services"].values():
        service["variables"] = VARIABLES[service["name"]]
        service["icon"] = ICON

    saved = rw.gql(
        """mutation($id: String!, $input: TemplateUpsertConfigInput!) {
             templateUpsertConfig(id: $id, input: $input) { id code }
           }""",
        {"id": template_id,
         "input": {"name": NAME, "workspaceId": WORKSPACE,
                   "serializedConfig": config, "canvasConfig": {}}},
        internal=True,
    )["templateUpsertConfig"]
    print(f"saved  id {saved['id']}  code {saved['code']}")

    # Read it back and assert field by field. A write that returned success is
    # not a write that landed.
    back = rw.gql("query($c: String!) { template(code: $c) { serializedConfig } }",
                  {"c": saved["code"]})["template"]["serializedConfig"]
    svc = next(iter(back["services"].values()))
    got = {k: v.get("defaultValue") for k, v in svc.get("variables", {}).items()}
    want = {k: v.get("defaultValue") for k, v in VARIABLES["octop"].items()}
    bad = {k for k, v in want.items() if v is not None and got.get(k) != v}
    assert not bad, f"variables did not land: {bad} (got {got})"
    assert got.get("OPENAI_API_KEY") is None or got["OPENAI_API_KEY"] == "", "OPENAI_API_KEY should be empty"
    print("read-back verified:", sorted(got))
    print("template id:", template_id)


if __name__ == "__main__":
    main()
