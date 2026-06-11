import { useEffect, useState } from "react";
import { useRunLogs } from "@/api/pipelines";

export function RunLog({ runId }: { runId: string }) {
  const [since, setSince] = useState(0);
  const [allLines, setAllLines] = useState<string[]>([]);
  const { data } = useRunLogs(runId, since);

  useEffect(() => {
    if (data?.lines.length) {
      setAllLines((prev) => [...prev, ...data.lines]);
      setSince(data.next_since);
    }
  }, [data]);

  return (
    <div className="h-64 overflow-y-auto border border-zinc-700 bg-zinc-950 p-3 font-data text-xs text-zinc-300">
      {allLines.length === 0 ? (
        <p className="text-zinc-500">Waiting for logs...</p>
      ) : (
        allLines.map((line, i) => <div key={i}>{line}</div>)
      )}
    </div>
  );
}
