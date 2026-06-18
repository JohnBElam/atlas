import { useCallback, useMemo, useRef } from "react";
import {
  DndContext,
  PointerSensor,
  useDraggable,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import {
  WidgetWrapper,
  WORKSHOP_CELL_PX,
  WORKSHOP_COLS,
} from "@/components/workshop/WidgetWrapper";
import type { LayoutItem, Widget } from "@/types/analytics";

function CanvasWidget({
  widget,
  layoutItem,
  allWidgets,
  selected,
  readOnly,
  onSelect,
  onResize,
}: {
  widget: Widget;
  layoutItem: LayoutItem;
  allWidgets: Widget[];
  selected: boolean;
  readOnly: boolean;
  onSelect: (widgetId: string) => void;
  onResize: (widgetId: string, w: number, h: number) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: layoutItem.widget_id,
    disabled: readOnly,
  });

  const resizeRef = useRef<{ startX: number; startY: number; startW: number; startH: number } | null>(
    null,
  );

  const style = useMemo(() => {
    const base = {
      position: "absolute" as const,
      left: layoutItem.x * WORKSHOP_CELL_PX,
      top: layoutItem.y * WORKSHOP_CELL_PX,
      width: layoutItem.w * WORKSHOP_CELL_PX,
      height: layoutItem.h * WORKSHOP_CELL_PX,
      zIndex: isDragging ? 20 : selected ? 10 : 1,
    };
    if (transform) {
      return {
        ...base,
        transform: CSS.Translate.toString(transform),
      };
    }
    return base;
  }, [layoutItem, transform, isDragging, selected]);

  const handleResizePointerDown = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (readOnly) return;
      e.stopPropagation();
      e.preventDefault();
      resizeRef.current = {
        startX: e.clientX,
        startY: e.clientY,
        startW: layoutItem.w,
        startH: layoutItem.h,
      };

      const onPointerMove = (ev: PointerEvent) => {
        if (!resizeRef.current) return;
        const dw = Math.round((ev.clientX - resizeRef.current.startX) / WORKSHOP_CELL_PX);
        const dh = Math.round((ev.clientY - resizeRef.current.startY) / WORKSHOP_CELL_PX);
        const nextW = Math.max(1, Math.min(WORKSHOP_COLS - layoutItem.x, resizeRef.current.startW + dw));
        const nextH = Math.max(1, resizeRef.current.startH + dh);
        onResize(layoutItem.widget_id, nextW, nextH);
      };

      const onPointerUp = () => {
        resizeRef.current = null;
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerUp);
      };

      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp);
    },
    [layoutItem, onResize, readOnly],
  );

  return (
    <div ref={setNodeRef} style={style}>
      <WidgetWrapper
        widget={widget}
        layout={{ ...layoutItem, x: 0, y: 0 }}
        allWidgets={allWidgets}
        selected={selected}
        readOnly={readOnly}
        dragHandleProps={readOnly ? undefined : { ...listeners, ...attributes }}
        onSelect={onSelect}
      />
      {!readOnly && (
        <div
          role="presentation"
          className="absolute bottom-0 right-0 z-20 h-3 w-3 cursor-se-resize border border-indigo-400 bg-indigo-600"
          onPointerDown={handleResizePointerDown}
        />
      )}
    </div>
  );
}

export function DashboardCanvas({
  layout,
  widgets,
  readOnly = false,
  selectedWidgetId,
  onSelect,
  onLayoutChange,
}: {
  layout: LayoutItem[];
  widgets: Widget[];
  readOnly?: boolean;
  selectedWidgetId: string | null;
  onSelect: (widgetId: string | null) => void;
  onLayoutChange: (layout: LayoutItem[]) => void;
}) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
  );

  const widgetsById = useMemo(() => {
    const map = new Map<string, Widget>();
    for (const widget of widgets) {
      map.set(widget.id, widget);
    }
    return map;
  }, [widgets]);

  const canvasHeight = useMemo(() => {
    if (layout.length === 0) {
      return WORKSHOP_CELL_PX * 4;
    }
    const maxBottom = Math.max(...layout.map((item) => (item.y + item.h) * WORKSHOP_CELL_PX));
    return Math.max(maxBottom, WORKSHOP_CELL_PX * 4);
  }, [layout]);

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, delta } = event;
      if (!delta.x && !delta.y) return;

      const dx = Math.round(delta.x / WORKSHOP_CELL_PX);
      const dy = Math.round(delta.y / WORKSHOP_CELL_PX);
      if (dx === 0 && dy === 0) return;

      onLayoutChange(
        layout.map((item) => {
          if (item.widget_id !== active.id) return item;
          const nextX = Math.max(0, Math.min(WORKSHOP_COLS - item.w, item.x + dx));
          const nextY = Math.max(0, item.y + dy);
          return { ...item, x: nextX, y: nextY };
        }),
      );
    },
    [layout, onLayoutChange],
  );

  const handleResize = useCallback(
    (widgetId: string, w: number, h: number) => {
      onLayoutChange(
        layout.map((item) =>
          item.widget_id === widgetId ? { ...item, w, h } : item,
        ),
      );
    },
    [layout, onLayoutChange],
  );

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div
        className="relative min-h-[320px] border border-zinc-700 bg-zinc-950"
        style={{
          minHeight: canvasHeight,
          backgroundImage:
            "linear-gradient(to right, rgb(63 63 70 / 0.35) 1px, transparent 1px), linear-gradient(to bottom, rgb(63 63 70 / 0.35) 1px, transparent 1px)",
          backgroundSize: `${WORKSHOP_CELL_PX}px ${WORKSHOP_CELL_PX}px`,
        }}
        onClick={() => {
          if (!readOnly) onSelect(null);
        }}
      >
        {layout.length === 0 && (
          <p className="absolute inset-0 flex items-center justify-center text-sm text-zinc-500">
            Empty canvas. Add a widget from the palette.
          </p>
        )}
        {layout.map((item) => {
          const widget = widgetsById.get(item.widget_id);
          if (!widget) return null;
          return (
            <CanvasWidget
              key={item.widget_id}
              widget={widget}
              layoutItem={item}
              allWidgets={widgets}
              selected={selectedWidgetId === widget.id}
              readOnly={readOnly}
              onSelect={onSelect}
              onResize={handleResize}
            />
          );
        })}
      </div>
    </DndContext>
  );
}
