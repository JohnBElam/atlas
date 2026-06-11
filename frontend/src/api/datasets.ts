import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteEnvelope, getEnvelope, postEnvelope, putEnvelope } from "./client";
import type { Dataset, DatasetPreview, DatasetProfile, IngestRequest } from "@/types/dataset";

export function useDatasets(search?: string, sourceId?: string) {
  return useQuery({
    queryKey: ["datasets", search, sourceId],
    queryFn: async () => {
      const res = await getEnvelope<Dataset[]>("/datasets", {
        page: 1,
        page_size: 100,
        search,
        source_id: sourceId,
      });
      return res.data ?? [];
    },
  });
}

export function useDataset(id: string) {
  return useQuery({
    queryKey: ["datasets", id],
    queryFn: async () => {
      const res = await getEnvelope<Dataset>(`/datasets/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useDatasetPreview(id: string, limit = 50) {
  return useQuery({
    queryKey: ["datasets", id, "preview", limit],
    queryFn: async () => {
      const res = await getEnvelope<DatasetPreview>(`/datasets/${id}/preview`, { limit });
      return res.data;
    },
    enabled: !!id,
  });
}

export function useDatasetProfile(id: string) {
  return useQuery({
    queryKey: ["datasets", id, "profile"],
    queryFn: async () => {
      const res = await getEnvelope<DatasetProfile>(`/datasets/${id}/profile`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useIngestDataset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: IngestRequest) => {
      const res = await postEnvelope<Dataset>("/datasets/ingest", body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["datasets"] }),
  });
}

export function useDeleteDataset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => deleteEnvelope<null>(`/datasets/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["datasets"] }),
  });
}

export function useUpdateDataset(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { display_name?: string; description?: string }) => {
      const res = await putEnvelope<Dataset>(`/datasets/${id}`, body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["datasets", id] }),
  });
}
