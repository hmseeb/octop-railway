#!/usr/bin/env python3
"""Publishes the template, then sets the icon separately (templateUpsertSettings,
which does not re-mint the slug). The slug is minted from NAME at first publish
and never moves, so this runs once, after the user confirms.
Usage: publish.py <templateId>
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path("~/.claude/skills/create-template-for-railway/scripts").expanduser()))
import rw  # noqa: E402

WORKSPACE = "fc4796db-2c6c-4354-a564-d4a1d900af53"  # Auromations
NAME = "Octop"
CATEGORY = "Other"
DESCRIPTION = "Multi-user self-hosted AI assistant: agents, IM channels, cron, browser"
# Square mark extracted from the upstream wordmark (its black text vanishes on
# Railway's dark canvas). Pinned to a commit in our own build repo; GitHub
# avatar URLs are rejected by this field.
ICON = "https://raw.githubusercontent.com/hmseeb/octop-railway/ea78288db80ac804a11a543847064d0ce96a0e86/assets/octop-icon.svg"

template_id = sys.argv[1]
readme = pathlib.Path(__file__).with_name("TEMPLATE_OVERVIEW.md").read_text()
assert len(DESCRIPTION) <= 75, f"description is {len(DESCRIPTION)} characters"
published = rw.gql(
    """mutation($id: String!, $input: TemplatePublishInput!) {
         templatePublish(id: $id, input: $input) { id code name isApproved }
       }""",
    {"id": template_id,
     "input": {"category": CATEGORY, "description": DESCRIPTION,
               "readme": readme, "workspaceId": WORKSPACE}},
)["templatePublish"]
print("published", published)
rw.gql(
    """mutation($id: String!, $input: TemplateUpsertSettingsInput!) {
         templateUpsertSettings(id: $id, input: $input) { id code image }
       }""",
    {"id": template_id, "input": {"name": NAME, "image": ICON}},
    internal=True,
)
print(f"icon set\nhttps://railway.com/deploy/{published['code']}")
