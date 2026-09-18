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
# Square org avatar; Railway rejects GitHub avatar URLs for the listing image in
# some templates, but this field took one for the service tile in repair.py. If
# publish rejects it, swap to a raw.githubusercontent asset pinned to a commit.
ICON = "https://avatars.githubusercontent.com/u/18470292?v=4"

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
