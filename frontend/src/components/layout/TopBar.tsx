export function TopBar({ title }: { title: string }) {
  return (
    <header className="flex h-14 items-center border-b border-zinc-700 bg-zinc-900 px-6">
      <h1 className="text-sm font-medium text-zinc-300">{title}</h1>
      <div className="ml-auto text-xs text-zinc-500">Local · Single user</div>
    </header>
  );
}
