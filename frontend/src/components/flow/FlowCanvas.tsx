import { ReactFlowProvider, useReactFlow } from "@xyflow/react";
import { useEffect } from "react";

function FitViewOnLoad({
  nodeCount,
  fitView,
}: {
  nodeCount: number;
  fitView: boolean;
}) {
  const { fitView: fitViewFn } = useReactFlow();

  useEffect(() => {
    if (!fitView || nodeCount <= 0) return;
    const frame = requestAnimationFrame(() => {
      void fitViewFn({ padding: 0.2, duration: 200 });
    });
    return () => cancelAnimationFrame(frame);
  }, [nodeCount, fitView, fitViewFn]);

  return null;
}

export function FlowCanvas({
  nodeCount,
  fitView = true,
  children,
}: {
  nodeCount: number;
  fitView?: boolean;
  children: React.ReactNode;
}) {
  return (
    <ReactFlowProvider>
      {children}
      <FitViewOnLoad nodeCount={nodeCount} fitView={fitView} />
    </ReactFlowProvider>
  );
}
