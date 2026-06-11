import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "danger";
  size?: "sm" | "md";
}

export function buttonClassName({
  variant = "default",
  size = "md",
  className,
}: {
  variant?: ButtonProps["variant"];
  size?: ButtonProps["size"];
  className?: string;
}) {
  return cn(
    "inline-flex items-center justify-center rounded-sm font-medium transition-colors disabled:opacity-50",
    size === "sm" ? "h-8 px-3 text-xs" : "h-9 px-4 text-sm",
    variant === "default" && "bg-indigo-600 text-white hover:bg-indigo-500",
    variant === "outline" && "border border-zinc-600 bg-transparent hover:bg-zinc-800",
    variant === "ghost" && "hover:bg-zinc-800",
    variant === "danger" && "bg-red-600 text-white hover:bg-red-500",
    className,
  );
}

export function Button({
  className,
  variant = "default",
  size = "md",
  ...props
}: ButtonProps) {
  return (
    <button
      className={buttonClassName({ variant, size, className })}
      {...props}
    />
  );
}
