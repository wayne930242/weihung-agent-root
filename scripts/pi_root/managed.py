"""Record a managed value's previous state once and restore it while the installed value is unchanged.

The marker keys are `previous_<name>`, `previous_<name>_present`, and `installed_<name>`; their names are
fixed by markers already on disk.
"""

from collections.abc import Iterable
from copy import deepcopy
from typing import Any

State = dict[str, Any]


def remember_keys(state: State, name: str, container: dict, keys: Iterable[str]) -> None:
    """Record each key's pre-install value once, including keys a later version starts managing."""
    first = f"previous_{name}" not in state
    previous = state.setdefault(f"previous_{name}", {})
    present = state.setdefault(f"previous_{name}_present", []) if first else state.get(f"previous_{name}_present")
    for key in keys:
        if key in previous:
            continue
        previous[key] = deepcopy(container.get(key))
        if present is not None and key in container:
            present.append(key)


def record_keys(state: State, name: str, container: dict, keys: Iterable[str]) -> None:
    state[f"installed_{name}"] = {key: deepcopy(container[key]) for key in keys}


def restore_keys(state: State, name: str, container: dict, keys: Iterable[str]) -> None:
    """Put back each key's pre-install value, or remove it, while it still holds what install wrote."""
    installed = state.get(f"installed_{name}", {})
    previous = state.get(f"previous_{name}", {})
    present = state.get(f"previous_{name}_present")
    for key in keys:
        if container.get(key) != installed.get(key):
            continue
        # Markers written before `previous_<name>_present` existed count a null previous value as absent.
        was_present = key in present if present is not None else previous.get(key) is not None
        if was_present:
            container[key] = previous.get(key)
        else:
            container.pop(key, None)


def restore_nested(container: dict, key: str, installed: Any, previous: Any, managed_keys: Iterable[str]) -> None:
    """Restore the managed keys inside `container[key]`, dropping the object once nothing is left in it."""
    current = container.get(key)
    if not isinstance(current, dict) or not isinstance(installed, dict):
        return
    restored = deepcopy(current)
    prior = previous if isinstance(previous, dict) else {}
    for name in managed_keys:
        if current.get(name) != installed.get(name):
            continue
        if name in prior:
            restored[name] = deepcopy(prior[name])
        else:
            restored.pop(name, None)
    if restored:
        container[key] = restored
    else:
        container.pop(key, None)


def restore_value(container: dict, key: str, installed: Any, previous: Any) -> None:
    """Put back a whole value install replaced, or remove it when there was none."""
    if container.get(key) != installed:
        return
    if previous is None:
        container.pop(key, None)
    else:
        container[key] = previous
