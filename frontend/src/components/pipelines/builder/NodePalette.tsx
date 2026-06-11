import { Button } from "@/components/ui/Button";
import type { PipelineDag } from "@/types/pipeline";

let nodeCounter = 1;

export function NodePalette({
  dag,
  onChange,
}: {
  dag: PipelineDag;
  onChange: (dag: PipelineDag) => void;
}) {
  const addNode = (type: "source" | "transform" | "output", transformType?: string) => {
    nodeCounter += 1;
    const id = `n${nodeCounter}`;
    const newNode =
      type === "source"
        ? { id, type: "source" as const, dataset_id: "" }
        : type === "transform"
          ? {
              id,
              type: "transform" as const,
              transform_type: transformType ?? "filter",
              config:
                transformType === "filter"
                  ? { conditions: [{ column: "id", operator: "is_not_null", value: null }] }
                  : {},
            }
          : {
              id,
              type: "output" as const,
              config: { namespace: "default", table_name: "output_table", mode: "overwrite" },
            };
    onChange({ ...dag, nodes: [...dag.nodes, newNode] });
  };

  return (
    <div className="space-y-2 border border-zinc-700 bg-zinc-900 p-3">
      <p className="text-xs text-zinc-500">Add nodes</p>
      <Button size="sm" variant="outline" onClick={() => addNode("source")}>
        Source
      </Button>
      <Button size="sm" variant="outline" onClick={() => addNode("transform", "filter")}>
        Filter
      </Button>
      <Button size="sm" variant="outline" onClick={() => addNode("output")}>
        Output
      </Button>
    </div>
  );
}
