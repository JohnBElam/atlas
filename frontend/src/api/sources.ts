import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient, deleteEnvelope, getEnvelope, postEnvelope, putEnvelope } from "./client";
import type { SchemaDiscovery, Source, TestConnectionResult } from "@/types/source";

export function useSources(search?: string) {
  return useQuery({
    queryKey: ["sources", search],
    queryFn: async () => {
      const res = await getEnvelope<Source[]>("/sources", { page: 1, page_size: 100, search });
      return res.data ?? [];
    },
  });
}

export function useSource(id: string) {
  return useQuery({
    queryKey: ["sources", id],
    queryFn: async () => {
      const res = await getEnvelope<Source>(`/sources/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name: string; source_type: string; config: Record<string, unknown> }) => {
      const res = await postEnvelope<Source>("/sources", body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });
}

export function useDeleteSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => deleteEnvelope<null>(`/sources/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });
}

export function useTestConnection(id: string) {
  return useMutation({
    mutationFn: async () => {
      const res = await postEnvelope<TestConnectionResult>(`/sources/${id}/test`);
      return res.data;
    },
  });
}

export function useDiscoverSchema(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (refresh: boolean = true) => {
      const res = await getEnvelope<SchemaDiscovery>(`/sources/${id}/schema`, {
        refresh,
      });
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources", id] }),
  });
}

export function useUploadFile(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const response = await apiClient.post(`/sources/${id}/upload`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      if (response.data.error) throw new Error(response.data.error);
      return response.data.data as { uploaded: boolean; filename: string };
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources", id] }),
  });
}

export function useUpdateSource(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name?: string; config?: Record<string, unknown> }) => {
      const res = await putEnvelope<Source>(`/sources/${id}`, body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources", id] }),
  });
}
