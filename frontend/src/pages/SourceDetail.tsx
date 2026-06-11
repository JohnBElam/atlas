import { useRef, useState } from "react";
import { useDiscoverSchema, useSource, useTestConnection, useUploadFile } from "@/api/sources";
import { useIngestDataset } from "@/api/datasets";
import { AppShell } from "@/components/layout/AppShell";
import { SchemaExplorer } from "@/components/sources/SchemaExplorer";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";

export function SourceDetailPage({ id }: { id: string }) {
  const { data: source, isLoading, isError, error } = useSource(id);
  const testConnection = useTestConnection(id);
  const discoverSchema = useDiscoverSchema(id);
  const uploadFile = useUploadFile(id);
  const ingest = useIngestDataset();
  const fileRef = useRef<HTMLInputElement>(null);
  const [ingestFile, setIngestFile] = useState("");
  const [datasetName, setDatasetName] = useState("");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [ingestSuccess, setIngestSuccess] = useState<string | null>(null);

  if (isLoading) {
    return (
      <AppShell title="Source">
        <Skeleton className="h-40 w-full" />
      </AppShell>
    );
  }

  if (isError) {
    return (
      <AppShell title="Source">
        <ErrorMessage message={getErrorMessage(error)} />
      </AppShell>
    );
  }

  if (!source) {
    return (
      <AppShell title="Source">
        <p className="text-red-400">Source not found.</p>
      </AppShell>
    );
  }

  const tables = source.schema_cache?.tables ?? [];

  return (
    <AppShell title={source.name}>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center gap-3">
          <Badge>{source.source_type}</Badge>
          <Button
            size="sm"
            variant="outline"
            onClick={() => testConnection.mutate()}
            disabled={testConnection.isPending}
          >
            Test Connection
          </Button>
          {testConnection.data && (
            <Badge variant={testConnection.data.connected ? "success" : "error"}>
              {testConnection.data.connected ? "Connected" : "Failed"}
            </Badge>
          )}
          <Button
            size="sm"
            onClick={() => discoverSchema.mutate(true)}
            disabled={discoverSchema.isPending}
          >
            Discover Schema
          </Button>
        </div>

        <div className="border border-zinc-700 bg-zinc-900 p-4">
          <h2 className="mb-3 text-sm font-medium">Upload file</h2>
          <input ref={fileRef} type="file" className="text-sm text-zinc-400" />
          <Button
            size="sm"
            className="mt-2"
            onClick={() => {
              const file = fileRef.current?.files?.[0];
              if (file) {
                setUploadError(null);
                uploadFile.mutate(file, {
                  onError: (err) => setUploadError(getErrorMessage(err)),
                });
              }
            }}
            disabled={uploadFile.isPending}
          >
            Upload
          </Button>
          {uploadError && <div className="mt-2"><ErrorMessage message={uploadError} /></div>}
        </div>

        <div className="border border-zinc-700 bg-zinc-900 p-4">
          <h2 className="mb-3 text-sm font-medium">Ingest to dataset</h2>
          <div className="flex flex-wrap gap-3">
            <Input
              placeholder="table_or_file (e.g. sample.csv)"
              value={ingestFile}
              onChange={(e) => setIngestFile(e.target.value)}
            />
            <Input
              placeholder="dataset_name"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
            />
            <Button
              onClick={() => {
                setIngestError(null);
                setIngestSuccess(null);
                ingest.mutate(
                  {
                    source_id: id,
                    table_or_file: ingestFile,
                    dataset_name: datasetName,
                    display_name: datasetName.replace(/_/g, " "),
                    mode: "create",
                  },
                  {
                    onSuccess: (dataset) => {
                      setIngestSuccess(dataset?.display_name ?? "Dataset created");
                      setIngestFile("");
                      setDatasetName("");
                    },
                    onError: (err) => setIngestError(getErrorMessage(err)),
                  },
                );
              }}
              disabled={!ingestFile || !datasetName || ingest.isPending}
            >
              Ingest
            </Button>
          </div>
          {ingestError && <div className="mt-3"><ErrorMessage message={ingestError} /></div>}
          {ingestSuccess && (
            <p className="mt-3 text-sm text-emerald-400">Created {ingestSuccess}</p>
          )}
        </div>

        <div>
          <h2 className="mb-3 text-sm font-medium">Schema</h2>
          <SchemaExplorer tables={discoverSchema.data?.tables ?? tables} />
        </div>
      </div>
    </AppShell>
  );
}
