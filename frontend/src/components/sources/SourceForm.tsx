import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  source_type: z.enum(["csv", "parquet", "postgresql"]),
  connection_string: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function SourceForm({
  onSubmit,
  loading,
}: {
  onSubmit: (values: { name: string; source_type: string; config: Record<string, unknown> }) => void;
  loading?: boolean;
}) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { source_type: "csv" },
  });

  const sourceType = watch("source_type");

  return (
    <form
      className="space-y-4 border border-zinc-700 bg-zinc-900 p-4"
      onSubmit={handleSubmit((values) => {
        const config: Record<string, unknown> = {};
        if (values.source_type === "postgresql" && values.connection_string) {
          config.connection_string = values.connection_string;
        }
        onSubmit({ name: values.name, source_type: values.source_type, config });
      })}
    >
      <div>
        <label className="mb-1 block text-xs text-zinc-400">Name</label>
        <Input {...register("name")} placeholder="demo_csv" />
        {errors.name && <p className="mt-1 text-xs text-red-400">{errors.name.message}</p>}
      </div>
      <div>
        <label className="mb-1 block text-xs text-zinc-400">Type</label>
        <select
          className="h-9 w-full rounded-sm border border-zinc-600 bg-zinc-900 px-3 text-sm"
          {...register("source_type")}
        >
          <option value="csv">CSV</option>
          <option value="parquet">Parquet</option>
          <option value="postgresql">PostgreSQL</option>
        </select>
      </div>
      {sourceType === "postgresql" && (
        <div>
          <label className="mb-1 block text-xs text-zinc-400">Connection string</label>
          <Input
            {...register("connection_string")}
            placeholder="postgresql://user:pass@host:5432/db"
          />
        </div>
      )}
      <Button type="submit" disabled={loading}>
        {loading ? "Creating..." : "Create Source"}
      </Button>
    </form>
  );
}
