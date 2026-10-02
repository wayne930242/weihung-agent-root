"""Record a managed key's previous value once and restore it while the installed value is unchanged."""

from copy import deepcopy


def remember_previous(state, name, settings, keys):
    """Record each managed key's pre-install value once, including keys a later version starts managing."""
    first = f"previous_{name}" not in state
    previous = state.setdefault(f"previous_{name}", {})
    present = state.setdefault(f"previous_{name}_present", []) if first else state.get(f"previous_{name}_present")
    for key in keys:
        if key in previous:
            continue
        previous[key] = deepcopy(settings.get(key))
        if present is not None and key in settings:
            present.append(key)


def restore_managed_keys(container, key, installed, previous, managed_keys):
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
