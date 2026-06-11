import { Link } from "@tanstack/react-router";
import { useState } from "react";
import {
  usePipeline,
  usePipelineRuns,
  useRunPipeline,
} from "@/api/pipelines";
import { AppShell } from "@/components/layout/AppShell";
import { RunLog } from "@/components/pipelines/RunLog";
import { RunStatusBadge } from "@/components/pipelines/RunStatusBadge";
import { Button, buttonClassName } from "@/components/ui/Button";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";

export function PipelineDetailPage({ id }: { id: string }) {
  const { data: pipeline, isLoading, isError, error } = usePipeline(id);
  const { data: runs } = usePipelineRuns(id);
  const runPipeline = useRunPipeline(id);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <AppShell title="Pipeline">
        <Skeleton className="h-40" />
      </AppShell>
    );
  }

  if (isError) {
    return (
      <AppShell title="Pipeline">
        <ErrorMessage message={getErrorMessage(error)} />
      </AppShell>
    );
  }

  if (!pipeline) {
    return (
      <AppShell title="Pipeline">
        <p className="text-red-400">Pipeline not found.</p>
      </AppShell>
    );
  }

  return (
    <AppShell title={pipeline.name}>
      <div className="mb-6 flex flex-wrap gap-3">
        <Link
          to="/pipelines/$id/builder"
          params={{ id }}
          className={buttonClassName({ variant: "outline" })}
        >
          Open Builder
        </Link>
        <Button
          onClick={() => {
            setRunError(null);
            runPipeline.mutate(undefined, {
              onSuccess: (data) => {
                if (data?.run_id) setActiveRunId(data.run_id);
              },
              onError: (err) => setRunError(getErrorMessage(err)),
            });
          }}
          disabled={runPipeline.isPending}
        >
          Run Pipeline
        </Button>
      </div>
      {runError && (
        <div className="mb-6">
          <ErrorMessage message={runError} />
        </div>
      )}

      <section className="mb-8">
        <h2 className="mb-3 text-sm font-medium">Recent runs</h2>
        <div className="space-y-2">
          {runs?.map((run) => (
            <button
              key={run.id}
              type="button"
              className="flex w-full items-center justify-between border border-zinc-700 bg-zinc-900 px-4 py-2 text-left hover:border-indigo-600"
              onClick={() => setActiveRunId(run.id)}
            >
              <span className="font-data text-xs text-zinc-400">
                {new Date(run.created_at).toLocaleString()}
              </span>
              <RunStatusBadge status={run.status} />
            </button>
          ))}
          {!runs?.length && <p className="text-sm text-zinc-500">No runs yet.</p>}
        </div>
      </section>

      {activeRunId && (
        <section>
          <h2 className="mb-3 text-sm font-medium">Run logs</h2>
          <RunLog runId={activeRunId} />
        </section>
      )}
    </AppShell>
  );
}
