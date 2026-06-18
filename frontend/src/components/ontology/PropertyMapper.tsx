import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useDatasets } from "@/api/datasets";
import { DatasetColumnSelect } from "@/components/ontology/DatasetColumnSelect";
import type { ObjectProperty } from "@/types/ontology";

export function PropertyMapper({
  properties,
  onAdd,
  onUpdate,
  onSetPrimaryKey,
  primaryKeyId,
  loading,
  addError,
  addResetSignal,
}: {
  properties: ObjectProperty[];
  onAdd: (body: {
    name: string;
    display_name: string;
    data_type: string;
    dataset_id?: string;
    column_name?: string;
  }) => void;
  addError?: string | null;
  addResetSignal?: number;
  onUpdate: (propertyId: string, body: { dataset_id?: string; column_name?: string }) => void;
  onSetPrimaryKey: (propertyId: string) => void;
  primaryKeyId: string | null;
  loading?: boolean;
}) {
  const { data: datasets } = useDatasets();
  const [addDatasetId, setAddDatasetId] = useState("");
  const [addColumnName, setAddColumnName] = useState("");
  const addFormRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (!addResetSignal) return;
    addFormRef.current?.reset();
    setAddDatasetId("");
    setAddColumnName("");
  }, [addResetSignal]);

  return (
    <div className="space-y-4">
      <form
        ref={addFormRef}
        className="grid gap-3 border border-zinc-700 bg-zinc-900 p-4 md:grid-cols-4"
        onSubmit={(e) => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget);
          onAdd({
            name: String(fd.get("name") ?? ""),
            display_name: String(fd.get("display_name") ?? ""),
            data_type: "string",
            dataset_id: addDatasetId || undefined,
            column_name: addColumnName || undefined,
          });
        }}
      >
        <Input name="name" placeholder="property_slug" required />
        <Input name="display_name" placeholder="Display Name" required />
        <select
          className="h-9 rounded-sm border border-zinc-600 bg-zinc-900 px-3 text-sm"
          value={addDatasetId}
          onChange={(e) => {
            setAddDatasetId(e.target.value);
            setAddColumnName("");
          }}
        >
          <option value="">Dataset</option>
          {datasets?.map((d) => (
            <option key={d.id} value={d.id}>
              {d.display_name}
            </option>
          ))}
        </select>
        <DatasetColumnSelect
          datasetId={addDatasetId}
          value={addColumnName}
          onChange={setAddColumnName}
          datasets={datasets}
        />
        <Button type="submit" disabled={loading} className="md:col-span-4">
          Add Property
        </Button>
        {addError && <p className="text-sm text-red-400 md:col-span-4">{addError}</p>}
      </form>

      <div className="space-y-2">
        {properties.map((prop) => (
          <div
            key={prop.id}
            className="flex flex-wrap items-center gap-3 border border-zinc-700 bg-zinc-900 p-3"
          >
            <span className="font-medium text-zinc-100">{prop.display_name}</span>
            <span className="font-data text-xs text-zinc-500">{prop.name}</span>
            <select
              className="h-8 rounded-sm border border-zinc-600 bg-zinc-950 px-2 text-xs"
              value={prop.dataset_id ?? ""}
              onChange={(e) =>
                onUpdate(prop.id, { dataset_id: e.target.value, column_name: "" })
              }
            >
              <option value="">Dataset</option>
              {datasets?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.display_name}
                </option>
              ))}
            </select>
            <DatasetColumnSelect
              datasetId={prop.dataset_id ?? ""}
              value={prop.column_name ?? ""}
              onChange={(columnName) =>
                onUpdate(prop.id, {
                  dataset_id: prop.dataset_id ?? undefined,
                  column_name: columnName,
                })
              }
              datasets={datasets}
              className="h-8 rounded-sm border border-zinc-600 bg-zinc-950 px-2 text-xs disabled:cursor-not-allowed disabled:opacity-50"
            />
            <Button
              size="sm"
              variant={primaryKeyId === prop.id ? "default" : "outline"}
              onClick={() => onSetPrimaryKey(prop.id)}
            >
              {primaryKeyId === prop.id ? "Primary Key" : "Set as PK"}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
