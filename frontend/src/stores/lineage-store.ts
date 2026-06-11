import { create } from "zustand";

interface LineageStore {
  selectedNodeId: string | null;
  setSelectedNodeId: (id: string | null) => void;
}

export const useLineageStore = create<LineageStore>((set) => ({
  selectedNodeId: null,
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
}));
