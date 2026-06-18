import { useEffect, useState } from "react";
import { useRunLogs } from "@/api/pipelines";
import { getWebSocketUrl } from "@/api/client";

type LogMode = "ws" | "poll";

interface WsLogMessage {
  lines?: string[];
  next_since?: number;
  type?: string;
  error?: string;
}

export function RunLog({ runId }: { runId: string }) {
  const [since, setSince] = useState(0);
  const [allLines, setAllLines] = useState<string[]>([]);
  const [mode, setMode] = useState<LogMode>("ws");
  const { data } = useRunLogs(runId, since, mode === "poll");

  useEffect(() => {
    setSince(0);
    setAllLines([]);
    setMode("ws");
  }, [runId]);

  useEffect(() => {
    if (mode !== "ws") return;

    let completed = false;
    const ws = new WebSocket(getWebSocketUrl(`/ws/pipeline-runs/${runId}`));

    ws.onmessage = (event) => {
      let payload: WsLogMessage;
      try {
        payload = JSON.parse(event.data as string) as WsLogMessage;
      } catch {
        setMode("poll");
        ws.close();
        return;
      }

      if (payload.error) {
        setMode("poll");
        ws.close();
        return;
      }

      if (payload.lines?.length) {
        setAllLines((prev) => [...prev, ...payload.lines!]);
        if (typeof payload.next_since === "number") {
          setSince(payload.next_since);
        }
      }

      if (payload.type === "done") {
        completed = true;
        ws.close();
      }
    };

    ws.onerror = () => {
      setMode("poll");
    };

    ws.onclose = () => {
      if (!completed) {
        setMode("poll");
      }
    };

    return () => {
      ws.close();
    };
  }, [runId, mode]);

  useEffect(() => {
    if (mode !== "poll" || !data?.lines.length) return;
    setAllLines((prev) => [...prev, ...data.lines]);
    setSince(data.next_since);
  }, [data, mode]);

  return (
    <div className="h-64 overflow-y-auto border border-zinc-700 bg-zinc-950 p-3 font-data text-xs text-zinc-300">
      <p className="mb-2 text-[10px] uppercase text-zinc-500">
        {mode === "ws" ? "Live" : "Polling"}
      </p>
      {allLines.length === 0 ? (
        <p className="text-zinc-500">Waiting for logs...</p>
      ) : (
        allLines.map((line, i) => <div key={i}>{line}</div>)
      )}
    </div>
  );
}
