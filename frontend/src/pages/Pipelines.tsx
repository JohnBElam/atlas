import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useCreatePipeline, usePipelines } from "@/api/pipelines";
import { AppShell } from "@/components/layout/AppShell";
import { PipelineCard } from "@/components/pipelines/PipelineCard";
import { Button } from "@/components/ui/Button";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";

export function PipelinesPage() {
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = usePipelines();
  const createPipeline = useCreatePipeline();
  const [name, setName] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);

  return (
    <AppShell title="Pipelines">
      <form
        className="mb-6 max-w-md space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          setCreateError(null);
          createPipeline.mutate(
            { name, dag_json: { nodes: [], edges: [] } },
            {
              onSuccess: (pipeline) => {
                setName("");
                if (pipeline?.id) {
                  void navigate({
                    to: "/pipelines/$id/builder",
                    params: { id: pipeline.id },
                  });
                }
              },
              onError: (err) => setCreateError(getErrorMessage(err)),
            },
          );
        }}
      >
        <div className="flex gap-3">
          <Input
            placeholder="Pipeline name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Button type="submit" disabled={!name || createPipeline.isPending}>
            Create
          </Button>
        </div>
        {createError && <ErrorMessage message={createError} />}
      </form>

      {isLoading ? (
        <Skeleton className="h-28 w-full max-w-sm" />
      ) : isError ? (
        <ErrorMessage message={getErrorMessage(error)} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.map((pipeline) => <PipelineCard key={pipeline.id} pipeline={pipeline} />)}
          {!data?.length && (
            <p className="text-sm text-zinc-500">
              No pipelines yet. Create one to open the builder.
            </p>
          )}
        </div>
      )}
    </AppShell>
  );
}
