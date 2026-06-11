import { useCallback, useEffect, useState } from "react";
import { usePipeline, useUpdatePipeline } from "@/api/pipelines";
import { AppShell } from "@/components/layout/AppShell";
import { NodeConfigPanel } from "@/components/pipelines/builder/NodeConfigPanel";
import { NodePalette } from "@/components/pipelines/builder/NodePalette";
import { PipelineCanvas } from "@/components/pipelines/builder/PipelineCanvas";
import { Button } from "@/components/ui/Button";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";
import type { PipelineDag } from "@/types/pipeline";

export function PipelineBuilderPage({ id }: { id: string }) {
  const { data: pipeline, isLoading, isError, error } = usePipeline(id);
  const updatePipeline = useUpdatePipeline(id);
  const [dag, setDag] = useState<PipelineDag>({ nodes: [], edges: [] });
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (pipeline) {
      setDag(pipeline.dag_json);
    }
  }, [pipeline]);

  const handleDagChange = useCallback((next: PipelineDag) => {
    setDag(next);
    setSaveSuccess(false);
  }, []);

  if (isLoading) {
    return (
      <AppShell title="Pipeline Builder">
        <Skeleton className="h-[500px]" />
      </AppShell>
    );
  }

  if (isError) {
    return (
      <AppShell title="Pipeline Builder">
        <ErrorMessage message={getErrorMessage(error)} />
      </AppShell>
    );
  }

  if (!pipeline) {
    return (
      <AppShell title="Pipeline Builder">
        <p className="text-red-400">Pipeline not found.</p>
      </AppShell>
    );
  }

  return (
    <AppShell title={`Builder · ${pipeline.name}`}>
      <div className="mb-4 flex items-center justify-end gap-3">
        {saveSuccess && <span className="text-sm text-emerald-400">Saved</span>}
        <Button
          onClick={() => {
            setSaveError(null);
            setSaveSuccess(false);
            updatePipeline.mutate(
              { dag_json: dag },
              {
                onSuccess: () => setSaveSuccess(true),
                onError: (err) => setSaveError(getErrorMessage(err)),
              },
            );
          }}
          disabled={updatePipeline.isPending}
        >
          Save DAG
        </Button>
      </div>
      {saveError && (
        <div className="mb-4">
          <ErrorMessage message={saveError} />
        </div>
      )}
      <div className="grid gap-4 lg:grid-cols-[200px_1fr_280px]">
        <NodePalette dag={dag} onChange={setDag} />
        <PipelineCanvas
          dag={dag}
          pipelineId={id}
          onChange={handleDagChange}
          onNodeSelect={setSelectedNodeId}
        />
        <NodeConfigPanel dag={dag} selectedNodeId={selectedNodeId} onChange={setDag} />
      </div>
    </AppShell>
  );
}
