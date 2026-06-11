import { cn } from "@/lib/utils";

export function Badge({
  children,
  variant = "default",
  className,
}: {
  children: React.ReactNode;
  variant?: "default" | "success" | "error" | "warning";
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-medium",
        variant === "default" && "bg-zinc-800 text-zinc-300 border border-zinc-600",
        variant === "success" && "bg-emerald-900 text-emerald-300 border border-emerald-600",
        variant === "error" && "bg-red-900 text-red-300 border border-red-600",
        variant === "warning" && "bg-amber-900 text-amber-300 border border-amber-600",
        className,
      )}
    >
      {children}
    </span>
  );
}
