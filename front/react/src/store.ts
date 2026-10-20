import { create } from 'zustand';

type UiState = {
  sidebarOpen: boolean;
  activeProjectId: number | null;
  setSidebarOpen: (open: boolean) => void;
  setActiveProjectId: (id: number | null) => void;
};

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  activeProjectId: null,
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  setActiveProjectId: (activeProjectId) => set({ activeProjectId }),
}));
