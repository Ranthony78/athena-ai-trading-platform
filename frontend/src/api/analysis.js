import api from "./axios";

export const analysisAPI = {
    getMarketDrivers: () => api.get("/ai/market-drivers/"),
    getLearning: (symbol, horizon) => api.get("/ai/learning/", { params: { symbol, horizon } }),
    preview: (data) => api.post("/ai/preview/", data, { timeout: 75_000 }),

    analyze: (data) =>
        // The backend allows Gemini 120 s and one retry after a timeout, so a
        // slow analysis can take about 4 minutes. Wait a little longer than
        // that so the browser doesn't abandon a request Athena is still processing.
        api.post("/ai/analyze/", data, { timeout: 270_000 }),

    getSessions: () => api.get("/ai/sessions/"),

    clearSessions: () => api.delete("/ai/sessions/"),

    getSession: (id) => api.get(`/ai/sessions/${id}/`),

    getSignals: () => api.get("/ai/signals/"),

    getTemplates: () => api.get("/ai/templates/"),

    getPreferences: () => api.get("/ai/preferences/"),

    savePreferences: (data) => api.put("/ai/preferences/", data),
};
