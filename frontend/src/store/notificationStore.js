import { create } from "zustand";

const useNotificationStore = create((set, get) => ({
    notifications: [],
    unreadCount: 0,

    setNotifications: (notifications) =>
        set({ notifications }),

    setUnreadCount: (count) =>
        set({ unreadCount: count }),

    addNotification: (notification) =>
        set((state) => ({
            notifications: [notification, ...state.notifications],
            unreadCount: state.unreadCount + 1,
        })),

    markRead: (id) =>
        set((state) => ({
            notifications: state.notifications.map((n) =>
                n.id === id ? { ...n, status: "READ" } : n
            ),
            unreadCount: Math.max(0, state.unreadCount - 1),
        })),

    markAllRead: () =>
        set((state) => ({
            notifications: state.notifications.map((n) => ({
                ...n,
                status: "READ",
            })),
            unreadCount: 0,
        })),
}));

export default useNotificationStore;