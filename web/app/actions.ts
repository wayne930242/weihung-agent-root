"use server";

import { revalidatePath } from "next/cache";
import { commitFile, readFile } from "@/lib/github";
import { PROFILE_PATH, applySwitch, taipeiToday } from "@/lib/profile";

export type SwitchState = {
  tone: "idle" | "ok" | "error";
  message: string;
};

export const initialSwitchState: SwitchState = { tone: "idle", message: "" };

export async function switchStrategy(
  _prev: SwitchState,
  formData: FormData,
): Promise<SwitchState> {
  const strategy = String(formData.get("strategy") ?? "").trim();
  const rationale = String(formData.get("rationale") ?? "").trim();

  if (!strategy) {
    return { tone: "error", message: "沒有指定策略" };
  }
  if (!rationale) {
    return {
      tone: "error",
      message: "請填寫選擇依據，這是 profile 的必要欄位",
    };
  }

  try {
    const file = await readFile(PROFILE_PATH);
    const activatedOn = taipeiToday();
    const text = applySwitch(file.text, strategy, activatedOn, rationale);

    if (text === file.text) {
      return { tone: "ok", message: "內容與現況相同，未產生 commit" };
    }

    await commitFile(
      { ...file, text },
      `chore(model-profile): 切換啟用策略至 ${strategy}`,
    );
    revalidatePath("/");

    return {
      tone: "ok",
      message: `已切換至 ${strategy}（${activatedOn}），下次開 session 會自動同步到本機`,
    };
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    // A 409 means the local checkout pushed between our read and our write.
    const hint = detail.includes("409")
      ? "：repo 在讀取後被改動過，請重新整理再試"
      : `：${detail}`;
    return { tone: "error", message: `切換失敗${hint}` };
  }
}
