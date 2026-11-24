import { describe, expect, it } from "vitest";
import { compareTier, overall } from "../lib/checker";

const min = { tier: "min" as const, cpu_ref: "intel-i5-8400", gpu_ref: "nvidia-gtx-1060-6gb", ram_gb: 8 };
const rec = { tier: "rec" as const, cpu_ref: "amd-ryzen-5-3600", gpu_ref: "nvidia-rtx-3060", ram_gb: 16 };

describe("checker", () => {
  it("meets recommended", () => {
    const pc = { cpu: "amd-ryzen-5-5600", gpu: "nvidia-rtx-3070", ramGb: 16 };
    expect(overall(compareTier(pc, min), compareTier(pc, rec))).toBe("recommended");
  });
  it("meets minimum only", () => {
    const pc = { cpu: "intel-i5-8400", gpu: "amd-rx-580-8gb", ramGb: 8 };
    expect(overall(compareTier(pc, min), compareTier(pc, rec))).toBe("minimum");
  });
  it("below minimum when any part fails", () => {
    const pc = { cpu: "intel-i5-8400", gpu: "nvidia-gtx-1050-ti", ramGb: 16 };
    const r = compareTier(pc, min);
    expect(r.verdict).toBe("fail");
    expect(r.parts.find((p) => p.part === "GPU")?.status).toBe("fail");
    expect(overall(r, compareTier(pc, rec))).toBe("below");
  });
  it("never guesses: unmapped requirement or unpicked part is unknown", () => {
    expect(compareTier({}, min).verdict).toBe("unknown");
    expect(compareTier({ cpu: "intel-i5-8400" }, { tier: "min" }).parts[0].status).toBe("unknown");
    expect(compareTier({}, undefined).verdict).toBe("unknown");
  });
  it("a failing part beats unknown parts", () => {
    expect(compareTier({ ramGb: 4 }, min).verdict).toBe("fail");
  });
});
