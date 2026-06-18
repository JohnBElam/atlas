import { create } from "zustand";

interface WorkshopStore {
  selectedWidgetId: string | null;
  setSelectedWidgetId: (id: string | null) => void;
  builderMode: "edit" | "view";
  setBuilderMode: (mode: "edit" | "view") => void;
  filterState: Record<string, string | string[]>;
  setFilterValue: (filterWidgetId: string, value: string | string[]) => void;
  resetFilterState: () => void;
}

export const useWorkshopStore = create<WorkshopStore>((set) => ({
  selectedWidgetId: null,
  setSelectedWidgetId: (id) => set({ selectedWidgetId: id }),
  builderMode: "edit",
  setBuilderMode: (mode) => set({ builderMode: mode }),
  filterState: {},
  setFilterValue: (filterWidgetId, value) =>
    set((state) => ({
      filterState: { ...state.filterState, [filterWidgetId]: value },
    })),
  resetFilterState: () => set({ filterState: {} }),
}));
