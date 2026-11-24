/** Shared Tailwind preset: maps CSS-variable tokens to utilities. */
const c = (name) => `rgb(var(--pb-${name}) / <alpha-value>)`;

module.exports = {
  darkMode: ["selector", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: c("bg"),
        surface: { 1: c("surface-1"), 2: c("surface-2"), 3: c("surface-3") },
        line: { DEFAULT: c("border"), strong: c("border-strong") },
        fg: { DEFAULT: c("text"), muted: c("text-muted") },
        accent: { DEFAULT: c("accent"), strong: c("accent-strong"), text: c("accent-text"), on: c("on-accent") },
        signal: { confirmed: c("confirmed"), reported: c("reported"), rumour: c("rumour"), alert: c("alert") },
      },
      fontFamily: {
        display: ["var(--font-display)", "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ["var(--font-body)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: { sm: "var(--pb-radius-sm)", DEFAULT: "var(--pb-radius)", lg: "var(--pb-radius-lg)" },
      boxShadow: { 1: "var(--pb-shadow-1)", 2: "var(--pb-shadow-2)", glow: "var(--pb-glow)" },
      transitionTimingFunction: { pb: "var(--pb-ease)" },
      transitionDuration: { fast: "var(--pb-dur-fast)", DEFAULT: "var(--pb-dur)", slow: "var(--pb-dur-slow)" },
      spacing: { gutter: "1rem" },
    },
  },
};
