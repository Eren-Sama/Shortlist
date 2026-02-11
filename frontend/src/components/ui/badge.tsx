"use client";

import { cn } from "@/lib/utils";

interface BadgeProps {
  variant?: "default" | "success" | "warning" | "error" | "info" | "accent";
  className?: string;
  children: React.ReactNode;
}

export function Badge({ variant = "default", className, children }: BadgeProps) {
  const variants = {
    default: "bg-raised text-secondary border-edge",
    success: "bg-ok-dim text-ok border-ok/20",
    warning: "bg-warn-dim text-warn border-warn/20",
    error: "bg-danger-dim text-danger border-danger/20",
    info: "bg-info-dim text-info border-info/20",
    accent: "bg-accent-dim text-accent border-accent/20",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
