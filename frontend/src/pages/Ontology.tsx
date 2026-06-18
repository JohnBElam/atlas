import { Link } from "@tanstack/react-router";
import { useState } from "react";
import {
  useCreateLink,
  useCreateObjectType,
  useLinkTypes,
  useObjectTypes,
  useOntologyGraph,
} from "@/api/ontology";
import { AppShell } from "@/components/layout/AppShell";
import { LinkTypeForm } from "@/components/ontology/LinkTypeForm";
import { ObjectTypeForm } from "@/components/ontology/ObjectTypeForm";
import { OntologyGraph } from "@/components/ontology/OntologyGraph";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";

export function OntologyPage() {
  const { data: types, isLoading, isError, error } = useObjectTypes();
  const { data: links } = useLinkTypes();
  const { data: graph } = useOntologyGraph();
  const createType = useCreateObjectType();
  const createLink = useCreateLink();
  const [showTypeForm, setShowTypeForm] = useState(false);
  const [showLinkForm, setShowLinkForm] = useState(false);
  const [createTypeError, setCreateTypeError] = useState<string | null>(null);
  const [createLinkError, setCreateLinkError] = useState<string | null>(null);

  const typeNameById = new Map(types?.map((t) => [t.id, t.display_name]) ?? []);

  return (
    <AppShell title="Ontology">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-zinc-400">
          Map datasets to business objects, then connect types with links.
        </p>
        <div className="flex gap-4">
          <button
            type="button"
            className="text-sm text-indigo-400 hover:text-indigo-300"
            onClick={() => setShowTypeForm((v) => !v)}
          >
            {showTypeForm ? "Hide type form" : "New type"}
          </button>
          <button
            type="button"
            className="text-sm text-indigo-400 hover:text-indigo-300"
            onClick={() => setShowLinkForm((v) => !v)}
          >
            {showLinkForm ? "Hide link form" : "New link"}
          </button>
        </div>
      </div>

      {showTypeForm && (
        <div className="mb-6 max-w-md space-y-3">
          <ObjectTypeForm
            loading={createType.isPending}
            onSubmit={(values) => {
              setCreateTypeError(null);
              createType.mutate(values, {
                onSuccess: () => {
                  setShowTypeForm(false);
                  setCreateTypeError(null);
                },
                onError: (err) => setCreateTypeError(getErrorMessage(err)),
              });
            }}
          />
          {createTypeError && <ErrorMessage message={createTypeError} />}
        </div>
      )}

      {showLinkForm && (
        <div className="mb-6 space-y-3">
          <LinkTypeForm
            loading={createLink.isPending}
            onSubmit={(body) => {
              setCreateLinkError(null);
              createLink.mutate(body, {
                onSuccess: () => {
                  setShowLinkForm(false);
                  setCreateLinkError(null);
                },
                onError: (err) => setCreateLinkError(getErrorMessage(err)),
              });
            }}
          />
          {createLinkError && <ErrorMessage message={createLinkError} />}
        </div>
      )}

      {graph && graph.nodes.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-3 text-sm font-medium">Graph</h2>
          <OntologyGraph graph={graph} />
        </div>
      )}

      {links && links.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-3 text-sm font-medium">Links</h2>
          <ul className="space-y-2">
            {links.map((link) => (
              <li
                key={link.id}
                className="border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-300"
              >
                <span className="font-medium text-zinc-100">
                  {typeNameById.get(link.from_object_type_id) ?? "?"}
                </span>
                <span className="mx-2 text-indigo-400">— {link.display_name} →</span>
                <span className="font-medium text-zinc-100">
                  {typeNameById.get(link.to_object_type_id) ?? "?"}
                </span>
                <span className="ml-2 font-data text-xs text-zinc-500">({link.cardinality})</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {isLoading ? (
        <Skeleton className="h-20" />
      ) : isError ? (
        <ErrorMessage message={getErrorMessage(error)} />
      ) : (
        <div>
          <h2 className="mb-3 text-sm font-medium">Object Types</h2>
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
            {!types?.length && (
              <p className="text-sm text-zinc-500">
                No object types yet. Run{" "}
                <code className="font-data text-xs text-zinc-400">
                  python backend/scripts/seed_ontology_demo.py
                </code>{" "}
                after ingesting demo datasets, or create a type manually.
              </p>
            )}
          </div>
        </div>
      )}
    </AppShell>
  );
}
