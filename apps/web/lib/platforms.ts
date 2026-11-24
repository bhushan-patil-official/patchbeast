export const PLATFORM_SHORT: Record<string, string> = { pc: "PC", ps5: "PS5", xbox_series: "Xbox", switch2: "Switch 2" };
/** schema.org gamePlatform values; only emitted for platforms with a Reported/Confirmed date. */
export const SCHEMA_PLATFORM: Record<string, string> = {
  pc: "PC game",
  ps5: "PlayStation 5",
  xbox_series: "Xbox Series X|S",
  switch2: "Nintendo Switch 2",
};
export const platformShort = (id: string) => PLATFORM_SHORT[id] ?? id;
