import { Link } from "@tanstack/react-router";
import { useObjectTypes, useOntologyGraph } from "@/api/ontology";
import { AppShell } from "@/components/layout/AppShell";
import { ObjectTypeForm } from "@/components/ontology/ObjectTypeForm";
import { OntologyGraph } from "@/components/ontology/OntologyGraph";
import { useCreateObjectType } from "@/api/ontology";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";
import { useState } from "react";

export function OntologyPage() {
  const { data: types, isLoading, isError, error } = useObjectTypes();
  const { data: graph } = useOntologyGraph();
  const createType = useCreateObjectType();
  const [showForm, setShowForm] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  return (
    <AppShell title="Ontology">
      <div className="mb-6 flex items-center justify-between">
        <p className="text-sm text-zinc-400">Define business object types and relationships.</p>
        <button
          type="button"
          className="text-sm text-indigo-400 hover:text-indigo-300"
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? "Hide form" : "New type"}
        </button>
      </div>

      {showForm && (
        <div className="mb-6 max-w-md space-y-3">
          <ObjectTypeForm
            loading={createType.isPending}
            onSubmit={(values) => {
              setCreateError(null);
              createType.mutate(values, {
                onSuccess: () => {
                  setShowForm(false);
                  setCreateError(null);
                },
                onError: (err) => setCreateError(getErrorMessage(err)),
              });
            }}
          />
          {createError && <ErrorMessage message={createError} />}
        </div>
      )}

      {graph && graph.nodes.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-3 text-sm font-medium">Graph</h2>
          <OntologyGraph graph={graph} />
        </div>
      )}

      {isLoading ? (
        <Skeleton className="h-20" />
      ) : isError ? (
        <ErrorMessage message={getErrorMessage(error)} />
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {types?.map((t) => (
            <Link
              key={t.id}
              to="/ontology/types/$id"
              params={{ id: t.id }}
              className="border border-zinc-700 bg-zinc-900 p-4 hover:border-indigo-600"
            >
              <h3 className="font-medium" style={{ color: t.color }}>
                {t.display_name}
              </h3>
              <p className="font-data text-xs text-zinc-500">{t.name}</p>
            </Link>
          ))}
          {!types?.length && <p className="text-sm text-zinc-500">No object types yet.</p>}
        </div>
      )}
    </AppShell>
  );
}
