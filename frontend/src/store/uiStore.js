import { create } from "zustand";
import { persist } from "zustand/middleware";

const useUIStore = create(
    persist(
        (set) => ({
            sidebarOpen: true,
            theme: "plum",
            loading: false,

            toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

            setSidebarOpen: (open) => set({ sidebarOpen: open }),

            setLoading: (loading) => set({ loading }),

            setTheme: (theme) => {
                if (!["light", "dark", "neon", "plum", "copper", "aurora", "ivory"].includes(theme))
                    return;
                document.documentElement.dataset.theme = theme;
                set({ theme });
            },
        }),
        {
            name: "athena-ui-preferences",
            version: 3,
            migrate: (persistedState, version) => {
                if (version < 2 && persistedState?.theme === "light") {
                    persistedState = { ...persistedState, theme: "plum" };
                }
                return persistedState;
            },
            partialize: (state) => ({ theme: state.theme, sidebarOpen: state.sidebarOpen }),
        }
    )
);

export default useUIStore;
