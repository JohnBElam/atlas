import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

const schema = z.object({
  name: z.string().min(1),
  display_name: z.string().min(1),
  description: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function ObjectTypeForm({
  onSubmit,
  loading,
}: {
  onSubmit: (values: FormValues) => void;
  loading?: boolean;
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  return (
    <form
      className="space-y-3 border border-zinc-700 bg-zinc-900 p-4"
      onSubmit={handleSubmit(onSubmit)}
    >
      <div>
        <label className="mb-1 block text-xs text-zinc-400">Slug name</label>
        <Input {...register("name")} placeholder="supplier" />
        {errors.name && <p className="text-xs text-red-400">{errors.name.message}</p>}
      </div>
      <div>
        <label className="mb-1 block text-xs text-zinc-400">Display name</label>
        <Input {...register("display_name")} placeholder="Supplier" />
      </div>
      <div>
        <label className="mb-1 block text-xs text-zinc-400">Description</label>
        <Input {...register("description")} />
      </div>
      <Button type="submit" disabled={loading}>
        {loading ? "Creating..." : "Create Object Type"}
      </Button>
    </form>
  );
}
