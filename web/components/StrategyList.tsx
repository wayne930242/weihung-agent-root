"use client";

import { useActionState, useState } from "react";
import { switchStrategy } from "@/app/actions";
import { initialSwitchState } from "@/lib/switch-state";

export type Strategy = {
  name: string;
  purpose: string;
  body: string;
};

export function StrategyList({
  strategies,
  active,
}: {
  strategies: Strategy[];
  active: string;
}) {
  const [state, formAction, pending] = useActionState(
    switchStrategy,
    initialSwitchState,
  );
  const [expanded, setExpanded] = useState<string | null>(null);
  const [switching, setSwitching] = useState<string | null>(null);

  return (
    <>
      {strategies.map((strategy) => {
        const isActive = strategy.name === active;
        const isOpen = expanded === strategy.name;
        const isSwitching = switching === strategy.name;

        return (
          <article key={strategy.name} className="row" data-active={isActive}>
            <div className="row-head">
              <h2 className="row-name">{strategy.name}</h2>
              {isActive && <span className="active-tag">啟用中</span>}
            </div>

            {strategy.purpose && (
              <p className="row-purpose">{strategy.purpose}</p>
            )}

            <div className="row-actions">
              <button
                type="button"
                aria-expanded={isOpen}
                onClick={() => setExpanded(isOpen ? null : strategy.name)}
              >
                {isOpen ? "收合內容" : "查看內容"}
              </button>

              {!isActive && (
                <button
                  type="button"
                  className={isSwitching ? "" : "accent"}
                  onClick={() =>
                    setSwitching(isSwitching ? null : strategy.name)
                  }
                >
                  {isSwitching ? "取消" : "切換到這套"}
                </button>
              )}
            </div>

            {isOpen && <pre>{strategy.body}</pre>}

            {isSwitching && (
              <form className="switch-form" action={formAction}>
                <input type="hidden" name="strategy" value={strategy.name} />
                <label htmlFor={`rationale-${strategy.name}`}>
                  選擇依據（會寫進 profile，說明為什麼這期換成這套）
                </label>
                <textarea
                  id={`rationale-${strategy.name}`}
                  name="rationale"
                  required
                  disabled={pending}
                  placeholder="例如：Codex 額度回補，複雜實作改回 Astra medium"
                />
                <div className="form-actions">
                  <button type="submit" className="accent" disabled={pending}>
                    {pending ? "commit 中…" : "確認切換並 commit"}
                  </button>
                </div>
              </form>
            )}
          </article>
        );
      })}

      {state.tone !== "idle" && (
        <p className="message" data-tone={state.tone}>
          {state.message}
        </p>
      )}
    </>
  );
}
