import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  useCreateProperty,
  useObjectList,
  useObjectType,
  useUpdateObjectType,
} from "@/api/ontology";
import { putEnvelope } from "@/api/client";
import type { ObjectProperty } from "@/types/ontology";
import { AppShell } from "@/components/layout/AppShell";
import { ObjectBrowser } from "@/components/ontology/ObjectBrowser";
import { PropertyMapper } from "@/components/ontology/PropertyMapper";
import { Skeleton } from "@/components/ui/Skeleton";

export function ObjectTypeDetailPage({ id }: { id: string }) {
  const { data, isLoading } = useObjectType(id);
  const createProperty = useCreateProperty(id);
  const updateType = useUpdateObjectType(id);
  const qc = useQueryClient();
  const updateProperty = useMutation({
    mutationFn: async ({
      propertyId,
      body,
    }: {
      propertyId: string;
      body: { dataset_id?: string; column_name?: string };
    }) => {
      const res = await putEnvelope<ObjectProperty>(`/ontology/properties/${propertyId}`, body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ontology", "types", id] }),
  });
  const [page, setPage] = useState(1);
  const {
    data: objectsResult,
    isLoading: objectsLoading,
    error: objectsError,
  } = useObjectList(id, page);

  if (isLoading) {
    return (
      <AppShell title="Object Type">
        <Skeleton className="h-40" />
      </AppShell>
    );
  }

  if (!data) {
    return (
      <AppShell title="Object Type">
        <p className="text-red-400">Object type not found.</p>
      </AppShell>
    );
  }

  const { type, properties } = data;
  const totalPages = Number(objectsResult?.meta?.total_pages ?? 1);

  return (
    <AppShell title={type.display_name}>
      <div className="space-y-8">
        <section>
          <h2 className="mb-3 text-sm font-medium">Properties</h2>
          <PropertyMapper
            properties={properties}
            primaryKeyId={type.primary_key_property_id}
            loading={createProperty.isPending}
            onAdd={(body) => createProperty.mutate(body)}
            onUpdate={(propertyId, body) => updateProperty.mutate({ propertyId, body })}
            onSetPrimaryKey={(propertyId) =>
              updateType.mutate({ primary_key_property_id: propertyId })
            }
          />
        </section>

        <section>
          <h2 className="mb-3 text-sm font-medium">Object Browser</h2>
          <ObjectBrowser
            columns={objectsResult?.data?.columns ?? []}
            rows={objectsResult?.data?.rows ?? []}
            loading={objectsLoading}
            error={
              objectsError instanceof Error ? objectsError.message : null
            }
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </section>
      </div>
    </AppShell>
  );
}
