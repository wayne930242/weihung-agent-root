"""What every install and uninstall step works on."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .jsonfile import write_json
from .paths import MARKER

State = dict[str, Any]


@dataclass
class Context:
    home: Path
    state: State
    skip_external: bool = False
    force: bool = False
    # The PI_HERDR_AGENTS_ROOT checkout replacing the pinned pi-herdr-agents release, if any.
    herdr_root: str | None = None
    first_install: bool = False
    # Company plugin checkouts an earlier install recorded and this machine no longer has.
    gone_plugins: list[str] = field(default_factory=list)

    @property
    def agent_dir(self) -> Path:
        return self.home / ".pi/agent"

    @property
    def settings_path(self) -> Path:
        return self.agent_dir / "settings.json"

    @property
    def herdr_config_path(self) -> Path:
        return self.agent_dir / "herdr-agents/config.json"

    def save(self) -> None:
        """Record progress, so a run that fails later still restores what this one changed."""
        write_json(self.home / MARKER, self.state)
