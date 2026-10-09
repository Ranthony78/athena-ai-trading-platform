import { create } from "zustand";
import { persist } from "zustand/middleware";

const useAuthStore = create(
    persist(
        (set) => ({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,

            login: (data) =>
                set({
                    user: data.user,
                    accessToken: data.access,
                    refreshToken: data.refresh,
                    isAuthenticated: true,
                }),

            logout: () =>
                set({
                    user: null,
                    accessToken: null,
                    refreshToken: null,
                    isAuthenticated: false,
                }),

            setAccessToken: (token) => set({ accessToken: token }),

            // Refresh rotates the refresh token (the old one is blacklisted),
            // so both must be stored together.
            setTokens: ({ access, refresh }) =>
                set((state) => ({
                    accessToken: access,
                    refreshToken: refresh || state.refreshToken,
                })),

            setUser: (user) => set({ user }),
        }),
        {
            name: "athena-auth",
            partialize: (state) => ({
                user: state.user,
                accessToken: state.accessToken,
                refreshToken: state.refreshToken,
                isAuthenticated: state.isAuthenticated,
            }),
        }
    )
);

// Keep every open tab in step. Another tab's token refresh (which cancels the
// old refresh token) or logout is written to localStorage; without this, a
// second tab kept its stale token in memory and its next refresh logged the
// user out of every tab (9 Oct, two tabs open).
if (typeof window !== "undefined") {
    window.addEventListener("storage", (event) => {
        if (event.key === "athena-auth") {
            useAuthStore.persist.rehydrate();
        }
    });
}

export default useAuthStore;
