"""The active model strategy: default model, enabled models, herdr-agents models, and tier roles."""

import hashlib
import re
from copy import deepcopy
from pathlib import Path

from .context import Context, State
from .jsonfile import read_json, write_json
from .managed import record_keys, remember_keys, restore_keys, restore_value
from .paths import PROFILE, ROLES_DIR, ROOT

Tiers = dict[str, list[str]]

OPUS_1M = "claude-bridge/claude-opus-5-5"
OPUS_200K = "claude-bridge/claude-200k-opus-5-5"
SONNET_1M = "claude-bridge/claude-sonnet-5-5"
HAIKU = "claude-bridge/claude-haiku-4-5"
LUNA = "openai-codex/gpt-6-luna"
# Only the coordinating session falls back to a 1M Opus; complex tiers fall back to the 200K twin.
ONE_M_TIERS = {"main"}
TIER_ROLES = {
    "docs": "Documentation, technical writing, formatting, and document conversion",
    "recon": "Investigation, codebase research, information organization, and source data processing",
    "ui": "UI/UX design review and visual inspection",
    "review": "Routine checks and code review",
    "simple": "Simple, localized, or mechanical code changes",
    "coding": "Standard feature implementation, refactoring, and large code work in a predictable environment",
    "complex_clear": "Complex work in an unpredictable environment, with clear instructions",
    "complex_unclear": "Complex work in an unpredictable environment, with unclear instructions or an ambiguous situation",
    "academic": "Academic research and forward-looking hard problems",
}
# Behavior roles carry no model of their own, so each uses the model of the tier that matches its work.
ROLE_TIERS = {"scout": "recon", "worker": "coding", "reviewer": "review", "adversarial-reviewer": "review",
              "visual-tester": "ui", "planner": "complex_unclear", "poteto": "complex_clear"}
FIELDS = ("defaultProvider", "defaultModel", "defaultThinkingLevel", "enabledModels")


def active_strategy() -> str:
    match = re.search(r"^Active strategy: \[[^]]+\]\(strategies/([^)]+)\)", PROFILE.read_text(), re.MULTILINE)
    if not match:
        raise ValueError("active strategy is missing from model-preference-profile.md")
    return match.group(1).removesuffix(".md")


def routing() -> tuple[str, list[str], Tiers, dict[str, list[str]]]:
    strategy = active_strategy()
    profiles = read_json(ROOT / "pi/model-profiles.json")
    if strategy not in profiles:
        raise ValueError(f"no Pi profile for strategy {strategy}")
    tiers = profiles[strategy]
    default = tiers["main"]
    categories = {name: tiers[name] for name in ("coding", "review", "recon", "docs")}
    categories.update(qa=tiers["review"], architecture=tiers["complex_unclear"])
    tasks = {name: candidates(model, name) for name, (model, _) in categories.items()}
    return strategy, default, tiers, tasks


def candidates(model: str, tier: str) -> list[str]:
    codex_fallback = {
        "docs": LUNA,
        "recon": LUNA,
        "simple": LUNA,
        "complex_unclear": "openai-codex/gpt-6-astra",
        "architecture": "openai-codex/gpt-6-astra",
        "academic": "openai-codex/gpt-6-astra",
    }.get(tier, "openai-codex/gpt-6.1-sol")
    if model.startswith("claude-bridge/"):
        other = codex_fallback
    elif model == LUNA:
        other = HAIKU
    else:
        other = OPUS_1M if tier in ONE_M_TIERS else OPUS_200K
    return list(dict.fromkeys((model, other)))


def default_candidates(default: list[str]) -> list[str]:
    return candidates(default[0], "main")


def enabled_models(default: list[str], tiers: Tiers) -> list[str]:
    """Every model a tier can dispatch to, so model cycling stays within the active strategy."""
    models = default_candidates(default)
    for name, (model, _) in tiers.items():
        if name != "main":
            models += candidates(model, name)
    return list(dict.fromkeys(models))


def tier_roles(tiers: Tiers) -> dict[str, str]:
    """The role definition of every tier but main, keyed by file name."""
    roles = {}
    for name, description in TIER_ROLES.items():
        model, thinking = tiers[name]
        roles[f"{name}.md"] = (f"---\nname: {name}\ndescription: {description}\n"
                               f"model: {', '.join(candidates(model, name))}\nthinking: {thinking}\n"
                               "auto-exit: true\nsystem-prompt: append\n---\n\n"
                               f"# {name} tier\n\nComplete the task in your task message within its stated scope, "
                               "verify the result, and report what you did and what you observed.\n")
    return roles


def write_tier_roles(home: Path, state: State, tiers: Tiers) -> None:
    """Replace the role files an earlier run wrote; a file this repository did not write stops the run."""
    roles_dir = home / ROLES_DIR
    owned = state.get("installed_roles", {})
    roles = tier_roles(tiers)
    for name in roles:
        path = roles_dir / name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != owned.get(name):
            raise ValueError(f"{path} was not written by this repository; move it, then rerun")
    for name in set(owned) - set(roles):
        (roles_dir / name).unlink(missing_ok=True)
    roles_dir.mkdir(parents=True, exist_ok=True)
    for name, content in roles.items():
        (roles_dir / name).write_text(content)
    state["installed_roles"] = {name: hashlib.sha256(content.encode()).hexdigest() for name, content in roles.items()}


def remove_tier_roles(home: Path, state: State) -> None:
    roles_dir = home / ROLES_DIR
    for name, digest in state.pop("installed_roles", {}).items():
        path = roles_dir / name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == digest:
            path.unlink()
    if roles_dir.exists() and not any(roles_dir.iterdir()):
        roles_dir.rmdir()


def update_profile(home: Path, state: State) -> None:
    """Point pi's default model, enabled models, herdr-agents models, and tier roles at the active strategy."""
    agent_dir = home / ".pi/agent"
    settings_path = agent_dir / "settings.json"
    config_path = agent_dir / "herdr-agents/config.json"
    settings = read_json(settings_path)
    config = read_json(config_path)
    strategy, default, tiers, tasks = routing()
    remember_keys(state, "settings", settings, FIELDS)
    state.setdefault("previous_models", deepcopy(config.get("models")))
    state.setdefault("previous_status", deepcopy(config.get("status")))
    provider, model = default[0].split("/", 1)
    settings.update(defaultProvider=provider, defaultModel=model, defaultThinkingLevel=default[1],
                    enabledModels=enabled_models(default, tiers))
    models = config.setdefault("models", {})
    models["default"] = ", ".join(default_candidates(default))
    # A role's model the user set by hand wins; only values an earlier run wrote follow the strategy.
    ours = state.get("installed_agent_models", {})
    agents = models.get("agents", {})
    managed = {role: ", ".join(candidates(tiers[tier][0], tier)) for role, tier in ROLE_TIERS.items()
               if role not in agents or agents[role] == ours.get(role)}
    models["agents"] = {**agents, **managed}
    state["installed_agent_models"] = managed
    models["tasks"] = tasks
    config.setdefault("status", {"enabled": True})
    write_json(settings_path, settings)
    write_json(config_path, config)
    write_tier_roles(home, state, tiers)
    record_keys(state, "settings", settings, FIELDS)
    state["installed_models"] = deepcopy(models)
    state["installed_status"] = deepcopy(config["status"])
    state["strategy"] = strategy


def apply(ctx: Context) -> None:
    update_profile(ctx.home, ctx.state)


def restore(ctx: Context) -> None:
    state = ctx.state
    remove_tier_roles(ctx.home, state)
    settings = read_json(ctx.settings_path)
    restore_keys(state, "settings", settings, FIELDS)
    write_json(ctx.settings_path, settings)
    config = read_json(ctx.herdr_config_path)
    restore_value(config, "models", state.get("installed_models"), state.get("previous_models"))
    restore_value(config, "status", state.get("installed_status"), state.get("previous_status"))
    if config:
        write_json(ctx.herdr_config_path, config)
    elif ctx.herdr_config_path.exists():
        ctx.herdr_config_path.unlink()
