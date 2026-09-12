import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { parseProfile, applySwitch } from '../web/lib/profile.ts';

const current = readFileSync(new URL('../skills/managing-model-preferences/model-preference-profile.md', import.meta.url), 'utf8');
const catalog = '\n## Strategies\n\n| Strategy | Purpose |\n|---|---|\n| [codex-first](strategies/codex-first.md) | Codex execution |\n';
const formats = {
  english: 'Active strategy: [codex-first](strategies/codex-first.md).\nActivated: 2026-09-12.\nRationale: Lower costs.\n',
  legacy: '目前最佳且啟用的策略：[codex-first](strategies/codex-first.md)。\n啟用日期：2026-09-12。\n選擇依據：降低費用。\n',
};

test('the actual profile provides all console fields', () => {
  const parsed = parseProfile(current);
  assert.ok(parsed.active);
  assert.match(parsed.activatedOn, /^\d{4}-\d{2}-\d{2}$/);
  assert.ok(parsed.rationale);
  assert.ok(parsed.purposes[parsed.active]);
});

for (const [format, header] of Object.entries(formats)) {
  test(`${format} profile supports display and switching without changing the catalog`, () => {
    const text = header + catalog;
    assert.equal(parseProfile(text).active, 'codex-first');
    assert.equal(parseProfile(text).activatedOn, '2026-09-12');
    const switched = applySwitch(text, 'claude-drive-codex', '2026-09-13', 'Save $5.');
    const parsed = parseProfile(switched);
    assert.equal(parsed.active, 'claude-drive-codex');
    assert.equal(parsed.activatedOn, '2026-09-13');
    assert.equal(parsed.rationale, 'Save $5.');
    assert.ok(switched.endsWith(catalog));
    assert.ok(switched.startsWith(format === 'english' ? 'Active strategy:' : '目前最佳且啟用的策略：'));
    assert.equal(applySwitch(switched, parsed.active, parsed.activatedOn, parsed.rationale), switched);
  });
}

test('an incomplete profile is rejected before switching', () => {
  assert.throws(() => applySwitch('## Strategies\n', 'codex-first', '2026-09-12', 'Costs'), /格式不符/);
});
