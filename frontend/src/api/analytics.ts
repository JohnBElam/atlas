import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteEnvelope, getEnvelope, postEnvelope, putEnvelope } from "./client";
import type {
  Dashboard,
  DashboardDetail,
  LayoutItem,
  Widget,
  WidgetData,
  WidgetFilterState,
  WidgetType,
} from "@/types/analytics";

export function useDashboards() {
  return useQuery({
    queryKey: ["dashboards"],
    queryFn: async () => {
      const res = await getEnvelope<Dashboard[]>("/analytics/dashboards", {
        page: 1,
        page_size: 100,
      });
      return res.data ?? [];
    },
  });
}

export function useDashboard(id: string) {
  return useQuery({
    queryKey: ["dashboards", id],
    queryFn: async () => {
      const res = await getEnvelope<DashboardDetail>(`/analytics/dashboards/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateDashboard() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name: string; description?: string }) => {
      const res = await postEnvelope<Dashboard>("/analytics/dashboards", body);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dashboards"] }),
  });
}

export function useUpdateDashboard(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      name?: string;
      description?: string | null;
      layout_json?: LayoutItem[];
    }) => {
      const res = await putEnvelope<Dashboard>(`/analytics/dashboards/${id}`, body);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dashboards"] });
      qc.invalidateQueries({ queryKey: ["dashboards", id] });
    },
  });
}

export function useDeleteDashboard() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => deleteEnvelope<null>(`/analytics/dashboards/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dashboards"] }),
  });
}

export function useCreateWidget(dashboardId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      widget_type: WidgetType;
      title?: string | null;
      config_json?: Record<string, unknown>;
      data_binding_json?: Record<string, unknown> | null;
    }) => {
      const res = await postEnvelope<Widget>(
        `/analytics/dashboards/${dashboardId}/widgets`,
        body,
      );
      return res.data;
    },
    onSuccess: (widget) => {
      if (!widget) return;
      qc.setQueryData<DashboardDetail>(["dashboards", dashboardId], (current) => {
        if (!current) return current;
        return {
          ...current,
          widgets: [...current.widgets, widget],
        };
      });
    },
  });
}

export function useUpdateWidget(dashboardId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      widgetId,
      body,
    }: {
      widgetId: string;
      body: {
        title?: string | null;
        config_json?: Record<string, unknown>;
        data_binding_json?: Record<string, unknown> | null;
      };
    }) => {
      const res = await putEnvelope<Widget>(`/analytics/widgets/${widgetId}`, body);
      return res.data;
    },
    onSuccess: (updated, variables) => {
      if (updated) {
        qc.setQueryData<DashboardDetail>(["dashboards", dashboardId], (current) => {
          if (!current) return current;
          return {
            ...current,
            widgets: current.widgets.map((w) =>
              w.id === variables.widgetId ? updated : w,
            ),
          };
        });
      }
      qc.invalidateQueries({ queryKey: ["widgets", variables.widgetId, "data"] });
    },
  });
}

export function useDeleteWidget(dashboardId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (widgetId: string) => deleteEnvelope<null>(`/analytics/widgets/${widgetId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dashboards", dashboardId] }),
  });
}

export function useWidgetData(
  widgetId: string,
  filters: WidgetFilterState = {},
  enabled = true,
) {
  return useQuery({
    queryKey: ["widgets", widgetId, "data", filters],
    queryFn: async () => {
      const res = await postEnvelope<WidgetData>(`/analytics/widgets/${widgetId}/data`, {
        filters,
      });
      return res.data;
    },
    enabled: enabled && !!widgetId,
  });
}
