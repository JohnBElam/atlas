import type { TableSchema } from "@/types/source";

export function SchemaExplorer({ tables }: { tables: TableSchema[] }) {
  if (!tables.length) {
    return <p className="text-sm text-zinc-500">No schema discovered yet.</p>;
  }

  return (
    <div className="space-y-4">
      {tables.map((table) => (
        <div key={table.name} className="border border-zinc-700 bg-zinc-900">
          <div className="border-b border-zinc-700 px-4 py-2 font-data text-sm text-indigo-300">
            {table.name}
          </div>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-xs text-zinc-500">
                <th className="px-4 py-2">Column</th>
                <th className="px-4 py-2">Type</th>
                <th className="px-4 py-2">Nullable</th>
              </tr>
            </thead>
            <tbody>
              {table.columns.map((col) => (
                <tr key={col.name} className="border-b border-zinc-800 font-data">
                  <td className="px-4 py-2">{col.name}</td>
                  <td className="px-4 py-2 text-zinc-400">{col.type}</td>
                  <td className="px-4 py-2">{col.nullable ? "yes" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
