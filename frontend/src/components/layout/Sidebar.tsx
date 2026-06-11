import { Link, useRouterState } from "@tanstack/react-router";
import {
  Database,
  GitBranch,
  Layers,
  Network,
  Shapes,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/sources", label: "Sources", icon: Database },
  { to: "/datasets", label: "Datasets", icon: Layers },
  { to: "/pipelines", label: "Pipelines", icon: GitBranch },
  { to: "/lineage", label: "Lineage", icon: Network },
  { to: "/ontology", label: "Ontology", icon: Shapes },
] as const;

export function Sidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-zinc-700 bg-zinc-900">
      <div className="border-b border-zinc-700 px-4 py-5">
        <span className="text-lg font-semibold tracking-wide text-indigo-400">ATLAS</span>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {navItems.map(({ to, label, icon: Icon }) => {
          const active = pathname === to || pathname.startsWith(`${to}/`);
          return (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex items-center gap-3 rounded-sm px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-indigo-600/20 text-indigo-300 border border-indigo-600"
                  : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
