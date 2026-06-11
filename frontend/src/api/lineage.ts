import { useQuery } from "@tanstack/react-query";
import { getEnvelope } from "./client";
import type { LineageGraph, SnapshotHistoryItem } from "@/types/lineage";

export function useLineageGraph() {
  return useQuery({
    queryKey: ["lineage", "graph"],
    queryFn: async () => {
      const res = await getEnvelope<LineageGraph>("/lineage/graph");
      return res.data;
    },
  });
}

export function useDatasetLineage(datasetId: string, hops = 3) {
  return useQuery({
    queryKey: ["lineage", "dataset", datasetId, hops],
    queryFn: async () => {
      const res = await getEnvelope<LineageGraph>(`/lineage/dataset/${datasetId}`, { hops });
      return res.data;
    },
    enabled: !!datasetId,
  });
}

export function useDatasetSnapshots(datasetId: string) {
  return useQuery({
    queryKey: ["lineage", "dataset", datasetId, "snapshots"],
    queryFn: async () => {
      const res = await getEnvelope<SnapshotHistoryItem[]>(
        `/lineage/dataset/${datasetId}/snapshots`,
      );
      return res.data ?? [];
    },
    enabled: !!datasetId,
  });
}
