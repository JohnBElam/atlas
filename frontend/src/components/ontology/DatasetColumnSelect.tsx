import type { Dataset } from "@/types/dataset";

function getSchemaColumns(datasets: Dataset[] | undefined, datasetId: string): string[] {
  const dataset = datasets?.find((d) => d.id === datasetId);
  return dataset?.schema_json?.fields?.map((field) => field.name).filter(Boolean) ?? [];
}

export function DatasetColumnSelect({
  datasetId,
  value,
  onChange,
  datasets,
  name,
  className,
}: {
  datasetId: string;
  value: string;
  onChange: (columnName: string) => void;
  datasets: Dataset[] | undefined;
  name?: string;
  className?: string;
}) {
  const columns = getSchemaColumns(datasets, datasetId);
  const disabled = !datasetId || columns.length === 0;
  const orphanValue = value && !columns.includes(value) ? value : null;

  return (
    <select
      name={name}
      className={
        className ??
        "h-9 rounded-sm border border-zinc-600 bg-zinc-900 px-3 text-sm disabled:cursor-not-allowed disabled:opacity-50"
      }
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">Column</option>
      {orphanValue && (
        <option value={orphanValue}>
          {orphanValue} (unmapped)
        </option>
      )}
      {columns.map((col) => (
        <option key={col} value={col}>
          {col}
        </option>
      ))}
    </select>
  );
}
