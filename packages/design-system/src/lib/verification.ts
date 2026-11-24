export type Verification = "confirmed" | "reported" | "rumour";

/** Confirmed = two independent sources or a video; Reported = one linked source; Rumour = unverified. */
export const VERIFICATION: Record<
  Verification,
  { label: string; bars: 1 | 2 | 3; text: string; bar: string; ring: string; help: string }
> = {
  confirmed: {
    label: "Confirmed",
    bars: 3,
    text: "text-signal-confirmed",
    bar: "bg-signal-confirmed",
    ring: "border-signal-confirmed/50",
    help: "Backed by two independent sources, or by a video.",
  },
  reported: {
    label: "Reported",
    bars: 2,
    text: "text-signal-reported",
    bar: "bg-signal-reported",
    ring: "border-signal-reported/50",
    help: "Backed by one linked source.",
  },
  rumour: {
    label: "Rumour",
    bars: 1,
    text: "text-signal-rumour",
    bar: "bg-signal-rumour",
    ring: "border-signal-rumour/50",
    help: "Unverified. Treat as speculation.",
  },
};

export const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;
