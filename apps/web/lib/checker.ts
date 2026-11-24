import { CPUS, GPUS, byId } from "@/data/hardware";

export interface UserPc {
  cpu?: string;
  gpu?: string;
  ramGb?: number;
}
export interface ReqRow {
  tier: "min" | "rec";
  cpu_ref?: string;
  gpu_ref?: string;
  ram_gb?: number | null;
}
export type PartStatus = "pass" | "fail" | "unknown";
export interface PartResult {
  part: "CPU" | "GPU" | "RAM";
  status: PartStatus;
  detail: string;
}
export interface TierResult {
  verdict: PartStatus;
  parts: PartResult[];
}

export function compareTier(pc: UserPc, req: ReqRow | undefined): TierResult {
  if (!req) return { verdict: "unknown", parts: [] };
  const parts: PartResult[] = [];

  const hw = (part: "CPU" | "GPU", list: typeof CPUS, mine?: string, need?: string): PartResult => {
    const m = byId(list, mine);
    const n = byId(list, need);
    if (!n) return { part, status: "unknown", detail: `Requirement not mapped to a ${part} tier yet.` };
    if (!m) return { part, status: "unknown", detail: `Pick your ${part} to compare.` };
    return m.score >= n.score
      ? { part, status: "pass", detail: `${m.name} is in the same tier or above ${n.name}.` }
      : { part, status: "fail", detail: `${m.name} is below ${n.name}.` };
  };
  parts.push(hw("CPU", CPUS, pc.cpu, req.cpu_ref));
  parts.push(hw("GPU", GPUS, pc.gpu, req.gpu_ref));
  if (!req.ram_gb) parts.push({ part: "RAM", status: "unknown", detail: "Memory requirement not published." });
  else if (!pc.ramGb) parts.push({ part: "RAM", status: "unknown", detail: "Pick your memory to compare." });
  else
    parts.push(
      pc.ramGb >= req.ram_gb
        ? { part: "RAM", status: "pass", detail: `${pc.ramGb} GB meets ${req.ram_gb} GB.` }
        : { part: "RAM", status: "fail", detail: `${pc.ramGb} GB is below ${req.ram_gb} GB.` },
    );

  const verdict: PartStatus = parts.some((p) => p.status === "fail")
    ? "fail"
    : parts.every((p) => p.status === "pass")
      ? "pass"
      : "unknown";
  return { verdict, parts };
}

export type Overall = "recommended" | "minimum" | "below" | "unknown";

export function overall(min: TierResult, rec: TierResult): Overall {
  if (rec.verdict === "pass") return "recommended";
  if (min.verdict === "pass") return "minimum";
  if (min.verdict === "fail") return "below";
  return "unknown";
}

export const OVERALL_COPY: Record<Overall, { title: string; body: string }> = {
  recommended: { title: "Meets recommended", body: "On paper, this PC meets the published recommended tier." },
  minimum: { title: "Meets minimum", body: "On paper, this PC meets the published minimum tier but not the recommended one." },
  below: { title: "Below minimum", body: "On paper, at least one part is below the published minimum." },
  unknown: { title: "Can't tell yet", body: "Some requirements or parts can't be compared automatically." },
};
