"""The model strategy: profiles, task fallbacks, and tier roles."""

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pi_root import profile
from pi_root.instructions import instructions as instructions_text
from support.pi import ROOT


class ProfileTests(unittest.TestCase):
    def test_strategy_tables_mirror_pi_profiles(self):
        preferences = ROOT / "skills/managing-model-preferences"
        profiles = json.loads((ROOT / "pi/model-profiles.json").read_text())
        catalog = (preferences / "model-preference-profile.md").read_text()
        self.assertEqual(sorted(path.stem for path in (preferences / "strategies").glob("*.md")), sorted(profiles))
        for name, tiers in profiles.items():
            with self.subTest(strategy=name):
                content = (preferences / f"strategies/{name}.md").read_text()
                rows = [line for line in content.splitlines() if line.startswith("| ") and "`" in line]
                expected = [f"| {tier} | `{model}` | {thinking} |" for tier, (model, thinking) in tiers.items()]
                self.assertEqual(rows, expected)
                self.assertIn(f"[{name}](strategies/{name}.md)", catalog)
                self.assertNotIn("agent-kind", content)

    def test_all_tiers_have_distinct_task_fallbacks(self):
        profiles = json.loads((ROOT / "pi/model-profiles.json").read_text())
        for strategy, tiers in profiles.items():
            with self.subTest(strategy=strategy):
                with mock.patch.object(profile, "active_strategy", lambda strategy=strategy: strategy):
                    _, default, _, tasks = profile.routing()
                self.assertEqual(set(tasks), {"coding", "review", "recon", "qa", "architecture", "docs"})
                for tier, candidates in tasks.items():
                    self.assertEqual(candidates[0], tiers.get(tier, tiers["review"] if tier == "qa" else tiers["complex_unclear"])[0])
                    self.assertEqual(len(candidates), len(set(candidates)))
                self.assertEqual(len(profile.default_candidates(default)), len(set(profile.default_candidates(default))))
                instructions = instructions_text()
                roles = profile.tier_roles(tiers)
                self.assertEqual(set(roles), {f"{tier}.md" for tier in tiers if tier != "main"})
                for tier, (model, thinking) in tiers.items():
                    self.assertNotIn(model, instructions)
                    if tier == "main":
                        continue
                    expected = ", ".join(profile.candidates(model, tier))
                    self.assertIn(f"\nname: {tier}\n", roles[f"{tier}.md"])
                    self.assertIn(f"\nmodel: {expected}\nthinking: {thinking}\n", roles[f"{tier}.md"])
                for role, tier in profile.ROLE_TIERS.items():
                    self.assertIn(tier, tiers, role)

    def test_only_main_falls_back_to_opus_1m(self):
        profiles = json.loads((ROOT / "pi/model-profiles.json").read_text())
        one_m = {"main", "complex_clear", "complex_unclear", "academic"}
        for strategy, tiers in profiles.items():
            for tier, (model, _) in tiers.items():
                with self.subTest(strategy=strategy, tier=tier):
                    self.assertNotEqual(model == profile.OPUS_1M and tier not in one_m, True)
                    if model == profile.LUNA:
                        self.assertEqual(profile.candidates(model, tier)[1], profile.HAIKU)
        self.assertEqual(profile.candidates("openai-codex/gpt-6.1-sol", "main")[1], profile.OPUS_1M)
        self.assertEqual(profile.candidates("openai-codex/gpt-6.1-sol", "complex_clear")[1], profile.OPUS_200K)
        self.assertEqual(profile.candidates("openai-codex/gpt-6-astra", "architecture")[1], profile.OPUS_200K)
        self.assertEqual(profile.candidates("openai-codex/gpt-6.1-sol", "review")[1], profile.OPUS_200K)
        self.assertEqual(profile.candidates("openai-codex/gpt-6.1-sol", "ui")[1], profile.OPUS_200K)


if __name__ == "__main__":
    unittest.main()
