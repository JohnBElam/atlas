import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getEnvelope, postEnvelope, putEnvelope } from "./client";
import type {
  LinkCardinality,
  LinkType,
  ObjectList,
  ObjectProperty,
  ObjectType,
  ObjectTypeDetail,
  OntologyGraph,
} from "@/types/ontology";

export function useObjectTypes() {
  return useQuery({
    queryKey: ["ontology", "types"],
    queryFn: async () => {
      const res = await getEnvelope<ObjectType[]>("/ontology/types", { page: 1, page_size: 100 });
      return res.data ?? [];
    },
  });
}

export function useObjectType(id: string) {
  return useQuery({
    queryKey: ["ontology", "types", id],
    queryFn: async () => {
      const res = await getEnvelope<ObjectTypeDetail>(`/ontology/types/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateObjectType() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      name: string;
      display_name: string;
      description?: string;
      icon?: string;
      color?: string;
    }) => {
      const res = await postEnvelope<ObjectType>("/ontology/types", body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ontology"] }),
  });
}

export function useUpdateObjectType(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      display_name?: string;
      description?: string;
      primary_key_property_id?: string;
    }) => {
      const res = await putEnvelope<ObjectType>(`/ontology/types/${id}`, body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ontology", "types", id] }),
  });
}

export function useCreateProperty(typeId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      name: string;
      display_name: string;
      data_type: string;
      dataset_id?: string;
      column_name?: string;
      sort_order?: number;
    }) => {
      const res = await postEnvelope<ObjectProperty>(`/ontology/types/${typeId}/properties`, body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ontology", "types", typeId] }),
  });
}

export function useUpdateProperty(propertyId: string, typeId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { dataset_id?: string; column_name?: string }) => {
      const res = await putEnvelope<ObjectProperty>(`/ontology/properties/${propertyId}`, body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ontology", "types", typeId] }),
  });
}

export function useOntologyGraph() {
  return useQuery({
    queryKey: ["ontology", "graph"],
    queryFn: async () => {
      const res = await getEnvelope<OntologyGraph>("/ontology/graph");
      return res.data;
    },
  });
}

export function useObjectList(typeId: string, page = 1, enabled = true) {
  return useQuery({
    queryKey: ["ontology", "types", typeId, "objects", page],
    queryFn: async () => {
      const res = await getEnvelope<ObjectList>(`/ontology/types/${typeId}/objects`, {
        page,
        page_size: 20,
      });
      return { data: res.data, meta: res.meta };
    },
    enabled: !!typeId && enabled,
    retry: false,
  });
}

export function useLinkTypes() {
  return useQuery({
    queryKey: ["ontology", "links"],
    queryFn: async () => {
      const res = await getEnvelope<LinkType[]>("/ontology/links");
      return res.data ?? [];
    },
  });
}

export function useCreateLink() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      name: string;
      display_name: string;
      from_object_type_id: string;
      to_object_type_id: string;
      cardinality: LinkCardinality;
      from_property_id: string;
      to_property_id: string;
    }) => {
      const res = await postEnvelope<LinkType>("/ontology/links", body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ontology"] }),
  });
}
