#!/usr/bin/env python3
"""Builds the live Octop source project in Auromations (the thing
templateGenerate later reads). One service, one volume, one domain.

Literal values are fine here except anything cross-service (none exist).
The admin password stays OUT of the source project on purpose: it is restored
as a ${{secret(32)}} generator during template repair, so every deployer gets
their own. The live project gets a random literal so it can boot for Phase 4
verification.
"""
import json
import pathlib
import secrets
import string
import sys

sys.path.insert(0, str(pathlib.Path("~/.claude/skills/create-template-for-railway/scripts").expanduser()))
import rw  # noqa: E402

WORKSPACE = "fc4796db-2c6c-4354-a564-d4a1d900af53"  # Auromations
IMAGE = "ghcr.io/hmseeb/octop-railway:1.0.0-r2"


def gql(doc, variables=None, internal=False):
    return rw.gql(doc, variables, internal=internal)


def main():
    proj = gql(
        'mutation($input: ProjectCreateInput!) { projectCreate(input: $input) { id name } }',
        {"input": {"workspaceId": WORKSPACE, "name": "octop-source",
                   "description": "Source project for the Octop template"}},
    )
    print("project:", proj)
    pid = proj["projectCreate"]["id"]

    env = gql('query($pid: String!) { project(id: $pid) { environments { edges { node { id name } } } } }', {"pid": pid})
    env_id = env["project"]["environments"]["edges"][0]["node"]["id"]
    print("environment:", env_id)

    pw = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
    variables = {
        "HOME": "/data",
        "PORT": "8088",
        "OCTOP_PORT": "8088",
        "OCTOP_BIND_HOST": "::",
        "OCTOP_ADMIN_USERNAME": "admin",
        "OCTOP_DEFAULT_PASSWORD": pw,
    }
    svc = gql(
        'mutation($input: ServiceCreateInput!) { serviceCreate(input: $input) { id name } }',
        {"input": {"projectId": pid, "name": "octop", "source": {"image": IMAGE},
                   "variables": variables}},
    )
    print("service:", svc)
    sid = svc["serviceCreate"]["id"]

    inst = gql(
        'mutation($sid: String!, $eid: String!, $input: ServiceInstanceUpdateInput!) '
        '{ serviceInstanceUpdate(serviceId: $sid, environmentId: $eid, input: $input) }',
        {"sid": sid, "eid": env_id, "input": {
            "startCommand": "/usr/local/bin/docker-entrypoint.sh",
            "healthcheckPath": "/api/health",
            "restartPolicyType": "ON_FAILURE",
            "numReplicas": 1,
        }},
    )
    print("instance:", inst)

    vol = gql(
        'mutation($input: VolumeCreateInput!) { volumeCreate(input: $input) { id name mountPath } }',
        {"input": {"projectId": pid, "environmentId": env_id, "serviceId": sid, "mountPath": "/data/.octop"}},
    )
    print("volume:", vol)

    dom = gql(
        'mutation($input: ServiceDomainCreateInput!) { serviceDomainCreate(input: $input) { id domain targetPort } }',
        {"input": {"serviceId": sid, "environmentId": env_id, "targetPort": 8088}},
    )
    print("domain:", dom)

    state = {"projectId": pid, "environmentId": env_id, "serviceId": sid,
             "domain": dom["serviceDomainCreate"]["domain"],
             "adminPassword": pw}
    pathlib.Path("live-state.json").write_text(json.dumps(state, indent=2))
    print("wrote live-state.json (contains the live admin password; purge in Phase 8)")


if __name__ == "__main__":
    main()
