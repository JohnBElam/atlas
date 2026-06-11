import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteEnvelope, getEnvelope, postEnvelope, putEnvelope } from "./client";
import type { Pipeline, PipelineDag, PipelineRun, RunLogs } from "@/types/pipeline";

export function usePipelines(search?: string) {
  return useQuery({
    queryKey: ["pipelines", search],
    queryFn: async () => {
      const res = await getEnvelope<Pipeline[]>("/pipelines", { page: 1, page_size: 100, search });
      return res.data ?? [];
    },
  });
}

export function usePipeline(id: string) {
  return useQuery({
    queryKey: ["pipelines", id],
    queryFn: async () => {
      const res = await getEnvelope<Pipeline>(`/pipelines/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreatePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name: string; description?: string; dag_json?: PipelineDag }) => {
      const res = await postEnvelope<Pipeline>("/pipelines", body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipelines"] }),
  });
}

export function useUpdatePipeline(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name?: string; description?: string; dag_json?: PipelineDag }) => {
      const res = await putEnvelope<Pipeline>(`/pipelines/${id}`, body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipelines", id] }),
  });
}

export function useDeletePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => deleteEnvelope<null>(`/pipelines/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipelines"] }),
  });
}

export function usePipelineRuns(pipelineId: string) {
  return useQuery({
    queryKey: ["pipelines", pipelineId, "runs"],
    queryFn: async () => {
      const res = await getEnvelope<PipelineRun[]>(`/pipelines/${pipelineId}/runs`, {
        page: 1,
        page_size: 20,
      });
      return res.data ?? [];
    },
    enabled: !!pipelineId,
    refetchInterval: 3000,
  });
}

export function usePipelineRun(runId: string) {
  return useQuery({
    queryKey: ["pipeline-runs", runId],
    queryFn: async () => {
      const res = await getEnvelope<PipelineRun>(`/pipelines/runs/${runId}`);
      return res.data;
    },
    enabled: !!runId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 2000 : false;
    },
  });
}

export function useRunPipeline(pipelineId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const res = await postEnvelope<{ run_id: string; status: string }>(
        `/pipelines/${pipelineId}/run`,
      );
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipelines", pipelineId, "runs"] });
    },
  });
}

export function useRunLogs(runId: string, since: number) {
  return useQuery({
    queryKey: ["pipeline-runs", runId, "logs", since],
    queryFn: async () => {
      const res = await getEnvelope<RunLogs>(`/pipelines/runs/${runId}/logs`, { since });
      return res.data;
    },
    enabled: !!runId,
    refetchInterval: 2000,
  });
}
