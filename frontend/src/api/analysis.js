import api from "./axios";

export const analysisAPI = {
    analyze: (data) =>
        api.post("/ai/analyze/", data),

    getSessions: () =>
        api.get("/ai/sessions/"),

    getSession: (id) =>
        api.get(`/ai/sessions/${id}/`),

    getSignals: () =>
        api.get("/ai/signals/"),

    getTemplates: () =>
        api.get("/ai/templates/"),
};