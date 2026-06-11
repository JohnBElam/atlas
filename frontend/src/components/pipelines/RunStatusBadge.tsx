import { Badge } from "@/components/ui/Badge";

export function RunStatusBadge({ status }: { status: string }) {
  const variant =
    status === "success"
      ? "success"
      : status === "failed"
        ? "error"
        : status === "running" || status === "queued"
          ? "warning"
          : "default";
  return <Badge variant={variant}>{status}</Badge>;
}
