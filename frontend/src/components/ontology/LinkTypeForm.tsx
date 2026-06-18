import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useObjectType, useObjectTypes } from "@/api/ontology";
import type { LinkCardinality } from "@/types/ontology";

const CARDINALITIES: LinkCardinality[] = ["one-to-one", "one-to-many", "many-to-many"];

export function LinkTypeForm({
  onSubmit,
  loading,
}: {
  onSubmit: (body: {
    name: string;
    display_name: string;
    from_object_type_id: string;
    to_object_type_id: string;
    cardinality: LinkCardinality;
    from_property_id: string;
    to_property_id: string;
  }) => void;
  loading?: boolean;
}) {
  const { data: types } = useObjectTypes();
  const [name, setName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [fromTypeId, setFromTypeId] = useState("");
  const [toTypeId, setToTypeId] = useState("");
  const [fromPropertyId, setFromPropertyId] = useState("");
  const [toPropertyId, setToPropertyId] = useState("");
  const [cardinality, setCardinality] = useState<LinkCardinality>("one-to-many");

  const { data: fromType } = useObjectType(fromTypeId);
  const { data: toType } = useObjectType(toTypeId);

  return (
    <form
      className="grid gap-3 border border-zinc-700 bg-zinc-900 p-4 md:grid-cols-2"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          name,
          display_name: displayName,
          from_object_type_id: fromTypeId,
          to_object_type_id: toTypeId,
          cardinality,
          from_property_id: fromPropertyId,
          to_property_id: toPropertyId,
        });
        setName("");
        setDisplayName("");
        setFromTypeId("");
        setToTypeId("");
        setFromPropertyId("");
        setToPropertyId("");
        setCardinality("one-to-many");
      }}
    >
      <Input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="link_slug"
        required
      />
      <Input
        value={displayName}
        onChange={(e) => setDisplayName(e.target.value)}
        placeholder="Display label on graph"
        required
      />
      <label className="block text-sm">
        <span className="mb-1 block text-xs text-zinc-400">From type</span>
        <select
          className="h-9 w-full rounded-sm border border-zinc-600 bg-zinc-900 px-3 text-sm"
          value={fromTypeId}
          onChange={(e) => {
            setFromTypeId(e.target.value);
            setFromPropertyId("");
          }}
          required
        >
          <option value="" disabled>
            Select type
          </option>
          {types?.map((t) => (
            <option key={t.id} value={t.id}>
              {t.display_name}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        <span className="mb-1 block text-xs text-zinc-400">To type</span>
        <select
          className="h-9 w-full rounded-sm border border-zinc-600 bg-zinc-900 px-3 text-sm"
          value={toTypeId}
          onChange={(e) => {
            setToTypeId(e.target.value);
            setToPropertyId("");
          }}
          required
        >
          <option value="" disabled>
            Select type
          </option>
          {types?.map((t) => (
            <option key={t.id} value={t.id}>
              {t.display_name}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        <span className="mb-1 block text-xs text-zinc-400">From property</span>
        <select
          className="h-9 w-full rounded-sm border border-zinc-600 bg-zinc-900 px-3 text-sm disabled:opacity-50"
          value={fromPropertyId}
          onChange={(e) => setFromPropertyId(e.target.value)}
          disabled={!fromTypeId}
          required
        >
          <option value="" disabled>
            {fromTypeId ? "Select property" : "Pick a type first"}
          </option>
          {fromType?.properties.map((p) => (
            <option key={p.id} value={p.id}>
              {p.display_name} ({p.column_name ?? "unmapped"})
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        <span className="mb-1 block text-xs text-zinc-400">To property</span>
        <select
          className="h-9 w-full rounded-sm border border-zinc-600 bg-zinc-900 px-3 text-sm disabled:opacity-50"
          value={toPropertyId}
          onChange={(e) => setToPropertyId(e.target.value)}
          disabled={!toTypeId}
          required
        >
          <option value="" disabled>
            {toTypeId ? "Select property" : "Pick a type first"}
          </option>
          {toType?.properties.map((p) => (
            <option key={p.id} value={p.id}>
              {p.display_name} ({p.column_name ?? "unmapped"})
            </option>
          ))}
        </select>
      </label>
      <select
        className="h-9 rounded-sm border border-zinc-600 bg-zinc-900 px-3 text-sm md:col-span-2"
        value={cardinality}
        onChange={(e) => setCardinality(e.target.value as LinkCardinality)}
      >
        {CARDINALITIES.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
      <Button type="submit" disabled={loading} className="md:col-span-2">
        {loading ? "Creating..." : "Create Link"}
      </Button>
    </form>
  );
}
