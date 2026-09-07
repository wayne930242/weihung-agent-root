export type SwitchState = {
  tone: "idle" | "ok" | "error";
  message: string;
};

// Lives outside actions.ts: a "use server" file may only export async
// functions, and a plain object there fails at request time, not build time.
export const initialSwitchState: SwitchState = { tone: "idle", message: "" };
