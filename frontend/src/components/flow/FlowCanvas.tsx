import { ReactFlowProvider, useReactFlow } from "@xyflow/react";
import { useEffect } from "react";

function FitViewOnLoad({ nodeCount }: { nodeCount: number }) {
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (nodeCount <= 0) return;
    const frame = requestAnimationFrame(() => {
      void fitView({ padding: 0.2, duration: 200 });
    });
    return () => cancelAnimationFrame(frame);
  }, [nodeCount, fitView]);

  return null;
}

export function FlowCanvas({
  nodeCount,
  children,
}: {
  nodeCount: number;
  children: React.ReactNode;
}) {
  return (
    <ReactFlowProvider>
      {children}
      <FitViewOnLoad nodeCount={nodeCount} />
    </ReactFlowProvider>
  );
}
