import api from "./axios";

export const notificationsAPI = {
    getNotifications: (params) =>
        api.get("/notifications/", { params }),

    markRead: (id) =>
        api.post(`/notifications/${id}/read/`),

    markAllRead: () =>
        api.post("/notifications/read-all/"),

    getPreferences: () =>
        api.get("/notifications/preferences/"),

    updatePreferences: (data) =>
        api.put("/notifications/preferences/", data),

    getAlerts: () =>
        api.get("/notifications/alerts/"),

    createAlert: (data) =>
        api.post("/notifications/alerts/", data),

    cancelAlert: (id) =>
        api.post(`/notifications/alerts/${id}/cancel/`),

    checkAlerts: () =>
        api.post("/notifications/alerts/check/"),
};