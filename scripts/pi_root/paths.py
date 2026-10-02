"""Where the repository, the marker, and the managed files live; roots other checkouts may override."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKER = Path(".pi/agent/.weihung-agent-root.json")
LOCAL_PACKAGE = str(ROOT)
# Testing an unreleased pi-herdr-agents fix: this variable names a checkout that replaces the pinned release.
HERDR_AGENTS_ROOT_VARIABLE = "PI_HERDR_AGENTS_ROOT"
AAAAV = Path(os.environ.get("PI_AAAAV_ROOT", ROOT.parent / "aaaav"))
# The pi-herdr-agents `models` object (role, default, and task models) this repository writes into its config.
HERDR_MODELS = ROOT / "pi/herdr-agents-models.json"
# The model strategy profile was removed; its generated tier roles and marker keys are retired on install.
RETIRED_ROLES_DIR = Path(".pi/agent/herdr-agents/roles")
LENS_CONFIG = Path(".pi-lens/config.json")
OPEN_TUI_CONFIG = Path(".pi/agent/open-tui.json")
MP_INFRA = ROOT.parent / "moldplan-center/plugins/waydosoft-marketplace/plugins/mp-infra"
SDLC = ROOT.parent / "moldplan-center/plugins/waydosoft-marketplace/plugins/sdlc"
TTT_PREFIX = Path(".local/share/weihung-agent-root/team-toon-tack")
# pi-skills ships bare skill directories without a pi manifest; its README installs it as a clone under the skills root.
PI_SKILLS_GIT = os.environ.get("PI_SKILLS_GIT", "https://github.com/badlogic/pi-skills.git")
PI_SKILLS_CLONE = Path(".local/share/weihung-agent-root/pi-skills")
# Company plugins are Pi packages inside the waydosoft-marketplace checkout; a machine without that checkout skips them.
COMPANY_PLUGINS = {"mp_infra": ("mp-infra", "PI_MP_INFRA_ROOT", MP_INFRA), "sdlc": ("sdlc", "PI_SDLC_ROOT", SDLC)}
