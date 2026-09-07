import { GitHubError, listMarkdown, readFile } from "@/lib/github";
import { PROFILE_PATH, STRATEGY_DIR, parseProfile } from "@/lib/profile";
import { StrategyList, type Strategy } from "@/components/StrategyList";

export const dynamic = "force-dynamic";

export default async function Page() {
  let profileText: string;
  let names: string[];

  try {
    [profileText, names] = await Promise.all([
      readFile(PROFILE_PATH).then((file) => file.text),
      listMarkdown(STRATEGY_DIR),
    ]);
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    const missingToken = error instanceof GitHubError && error.status === 500;

    return (
      <div className="error-page">
        <h2>讀不到 repo</h2>
        <p>
          {missingToken
            ? "GITHUB_TOKEN 未設定。在 Vercel 專案的 Environment Variables 加上具 Contents: Read and write 權限的 fine-grained token。"
            : detail}
        </p>
      </div>
    );
  }

  const profile = parseProfile(profileText);
  const bodies = await Promise.all(
    names.map((name) => readFile(`${STRATEGY_DIR}/${name}.md`)),
  );

  const strategies: Strategy[] = names.map((name, i) => ({
    name,
    purpose: profile.purposes[name] ?? "",
    body: bodies[i].text,
  }));

  return (
    <>
      <h1>模型偏好主控台</h1>

      <section className="active-card">
        <p className="active-label">目前啟用</p>
        <p className="active-name">{profile.active || "（無法解析）"}</p>
        <p className="active-meta">啟用日期 {profile.activatedOn || "—"}</p>
        <p className="active-rationale">{profile.rationale}</p>
      </section>

      <p className="section-label">策略目錄</p>
      <StrategyList strategies={strategies} active={profile.active} />
    </>
  );
}
