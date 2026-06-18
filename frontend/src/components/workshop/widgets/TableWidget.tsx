import { useEffect, useRef } from "react";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import { useWidgetData } from "@/api/analytics";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";
import { parseDataBinding, type Widget, type WidgetFilterState } from "@/types/analytics";

const VIRTUAL_THRESHOLD = 500;

export function TableWidget({
  widget,
  filters = {},
  onError,
}: {
  widget: Widget;
  filters?: WidgetFilterState;
  onError?: (message: string | null) => void;
}) {
  const binding = parseDataBinding(widget.data_binding_json);
  const hasBinding = binding?.source_type === "dataset" && !!binding.dataset_id;
  const { data, isLoading, isError, error } = useWidgetData(widget.id, filters, hasBinding);

  useEffect(() => {
    onError?.(isError ? getErrorMessage(error) : null);
  }, [isError, error, onError]);

  if (!hasBinding) {
    return <p className="text-xs text-zinc-500">Select a dataset in Data Binding.</p>;
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-6 w-full" />
        <Skeleton className="h-6 w-full" />
        <Skeleton className="h-6 w-full" />
      </div>
    );
  }

  if (isError) {
    return <p className="text-xs text-red-400">{getErrorMessage(error)}</p>;
  }

  if (!data || data.rows.length === 0) {
    return <p className="text-xs text-zinc-500">No rows to display.</p>;
  }

  if (data.rows.length > VIRTUAL_THRESHOLD) {
    return <VirtualTable columns={data.columns} rows={data.rows} />;
  }

  return <SimpleTable columns={data.columns} rows={data.rows} />;
}

function SimpleTable({
  columns,
  rows,
}: {
  columns: string[];
  rows: Record<string, unknown>[];
}) {
  return (
    <table className="w-full text-left text-xs">
      <thead>
        <tr className="border-b border-zinc-700 text-zinc-500">
          {columns.map((col) => (
            <th key={col} className="px-2 py-1 font-data font-medium">
              {col}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} className="border-b border-zinc-800 font-data text-zinc-300">
            {columns.map((col) => (
              <td key={col} className="px-2 py-1">
                {String(row[col] ?? "")}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function VirtualTable({
  columns,
  rows,
}: {
  columns: string[];
  rows: Record<string, unknown>[];
}) {
  const parentRef = useRef<HTMLDivElement>(null);
  const columnDefs: ColumnDef<Record<string, unknown>>[] = columns.map((col) => ({
    accessorKey: col,
    header: col,
    cell: (info) => String(info.getValue() ?? ""),
  }));

  const table = useReactTable({
    data: rows,
    columns: columnDefs,
    getCoreRowModel: getCoreRowModel(),
  });

  const tableRows = table.getRowModel().rows;
  const virtualizer = useVirtualizer({
    count: tableRows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 32,
    overscan: 10,
  });

  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <table className="w-full text-left text-xs">
        <thead className="sticky top-0 bg-zinc-900">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className="border-b border-zinc-700 text-zinc-500">
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="px-2 py-1 font-data font-medium">
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {virtualizer.getVirtualItems().length > 0 && (
            <tr style={{ height: virtualizer.getVirtualItems()[0]?.start ?? 0 }}>
              <td colSpan={columns.length} />
            </tr>
          )}
          {virtualizer.getVirtualItems().map((virtualRow) => {
            const row = tableRows[virtualRow.index];
            if (!row) return null;
            return (
              <tr
                key={row.id}
                className="border-b border-zinc-800 font-data text-zinc-300"
                style={{ height: `${virtualRow.size}px` }}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-2 py-1">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
