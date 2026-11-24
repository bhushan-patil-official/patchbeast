import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "../lib/cn";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md";
  asChild?: boolean;
}

const base =
  "pb-focus inline-flex items-center justify-center gap-2 rounded font-medium transition-colors duration-fast ease-pb disabled:opacity-50 disabled:pointer-events-none";
const variants = {
  primary: "bg-accent-strong text-accent-on hover:bg-accent-strong/90 shadow-1",
  secondary: "bg-surface-2 text-fg border border-line hover:border-line-strong hover:bg-surface-3",
  ghost: "text-fg-muted hover:text-fg hover:bg-surface-2",
};
const sizes = { sm: "h-8 px-3 text-sm", md: "h-10 px-4 text-sm" };

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", size = "md", asChild, ...props },
  ref,
) {
  const Comp = asChild ? Slot : "button";
  return <Comp ref={ref} className={cn(base, variants[variant], sizes[size], className)} {...props} />;
});
