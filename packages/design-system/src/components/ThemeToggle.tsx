"use client";
import * as React from "react";
import { cn } from "../lib/cn";

type Theme = "dark" | "light";

/** Inline script (render in <head>) that applies the saved theme before paint: no flash. */
export const themeInitScript = `try{var t=localStorage.getItem("pb-theme");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}catch(e){}`;

export function ThemeToggle({ className }: { className?: string }) {
  const [theme, setTheme] = React.useState<Theme>("dark");
  React.useEffect(() => {
    setTheme(document.documentElement.dataset.theme === "light" ? "light" : "dark");
  }, []);
  const toggle = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("pb-theme", next);
    } catch {
      /* storage may be blocked; theme still applies for this visit */
    }
    setTheme(next);
  };
  return (
    <button
      type="button"
      onClick={toggle}
      // accessible name starts with the visible label (WCAG 2.5.3 Label in Name)
      aria-label={`${theme === "light" ? "Light" : "Dark"} theme, switch to ${theme === "light" ? "dark" : "light"}`}
      className={cn(
        "pb-focus inline-flex h-8 items-center gap-2 rounded border border-line bg-surface-2 px-2.5 text-xs text-fg-muted hover:text-fg",
        className,
      )}
    >
      <span aria-hidden="true">{theme === "light" ? "☀" : "☾"}</span>
      <span>{theme === "light" ? "Light" : "Dark"}</span>
    </button>
  );
}
