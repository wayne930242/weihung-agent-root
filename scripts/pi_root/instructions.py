"""The generated ~/.pi/agent/AGENTS.md."""

from .paths import ROOT


def instructions():
    return (ROOT / "pi/AGENTS.md.in").read_text().rstrip() + "\n"
