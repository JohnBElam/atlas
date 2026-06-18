import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { parseTextConfig, type Widget } from "@/types/analytics";

export function TextWidget({ widget }: { widget: Widget }) {
  const config = parseTextConfig(widget.config_json);

  if (!config.content.trim()) {
    return <p className="text-xs text-zinc-500">Add Markdown content in Display.</p>;
  }

  return (
    <div className="text-sm text-zinc-200">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="mb-2 text-lg font-semibold text-zinc-100">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="mb-2 text-base font-semibold text-zinc-100">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="mb-1 text-sm font-semibold text-zinc-100">{children}</h3>
          ),
          p: ({ children }) => <p className="mb-2 leading-relaxed text-zinc-300">{children}</p>,
          ul: ({ children }) => (
            <ul className="mb-2 list-disc space-y-1 pl-4 text-zinc-300">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-2 list-decimal space-y-1 pl-4 text-zinc-300">{children}</ol>
          ),
          li: ({ children }) => <li className="text-zinc-300">{children}</li>,
          strong: ({ children }) => (
            <strong className="font-semibold text-zinc-100">{children}</strong>
          ),
          em: ({ children }) => <em className="italic text-zinc-300">{children}</em>,
          a: ({ href, children }) => (
            <a href={href} className="text-indigo-400 hover:text-indigo-300">
              {children}
            </a>
          ),
          code: ({ children }) => (
            <code className="bg-zinc-800 px-1 py-0.5 font-data text-xs text-indigo-300">
              {children}
            </code>
          ),
        }}
      >
        {config.content}
      </ReactMarkdown>
    </div>
  );
}
