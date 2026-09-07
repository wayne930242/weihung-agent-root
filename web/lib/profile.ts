export const PROFILE_PATH =
  "skills/managing-model-preferences/model-preference-profile.md";
export const STRATEGY_DIR = "skills/managing-model-preferences/strategies";

const ACTIVE_RE = /目前最佳且啟用的策略：\[([^\]]+)\]\(strategies\/([^)]+)\)。/;
const DATE_RE = /啟用日期：([^\n]*?)。/;
const RATIONALE_RE = /選擇依據：([^\n]*)/;
const CATALOG_ROW_RE = /^\|\s*\[([^\]]+)\]\([^)]*\)\s*\|\s*(.+?)\s*\|\s*$/gm;

export type Profile = {
  active: string;
  activatedOn: string;
  rationale: string;
  purposes: Record<string, string>;
};

export function parseProfile(text: string): Profile {
  const active = ACTIVE_RE.exec(text);
  const date = DATE_RE.exec(text);
  const rationale = RATIONALE_RE.exec(text);

  const purposes: Record<string, string> = {};
  for (const row of text.matchAll(CATALOG_ROW_RE)) {
    purposes[row[1]] = row[2];
  }

  return {
    active: active?.[1] ?? "",
    activatedOn: date?.[1] ?? "",
    rationale: rationale?.[1] ?? "",
    purposes,
  };
}

/**
 * Rewrites only the three lines the skill defines as the switch: the active
 * link, the date, and the rationale. Every strategy file and the catalog table
 * stay untouched.
 */
export function applySwitch(
  text: string,
  strategy: string,
  activatedOn: string,
  rationale: string,
): string {
  if (
    !ACTIVE_RE.test(text) ||
    !DATE_RE.test(text) ||
    !RATIONALE_RE.test(text)
  ) {
    throw new Error("profile 格式不符預期，未做任何修改");
  }

  const trimmed = rationale.trim();
  const tail = /[。．.!?！？]$/.test(trimmed) ? "" : "。";

  // Function replacements, because a `$` in the rationale is a substitution
  // pattern in a string replacement and would be silently eaten.
  return text
    .replace(
      ACTIVE_RE,
      () => `目前最佳且啟用的策略：[${strategy}](strategies/${strategy}.md)。`,
    )
    .replace(DATE_RE, () => `啟用日期：${activatedOn}。`)
    .replace(RATIONALE_RE, () => `選擇依據：${trimmed}${tail}`);
}

export function taipeiToday(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Taipei",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}
