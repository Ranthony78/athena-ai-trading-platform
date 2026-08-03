import { create } from "zustand";

const useUIStore = create((set) => ({
    sidebarOpen: true,
    theme: "dark",
    loading: false,

    toggleSidebar: () =>
        set((state) => ({ sidebarOpen: !state.sidebarOpen })),

    setSidebarOpen: (open) =>
        set({ sidebarOpen: open }),

    setLoading: (loading) =>
        set({ loading }),
}));

export default useUIStore;