import api from "./axios";

export const analysisAPI = {
    getMarketDrivers: () => api.get("/ai/market-drivers/"),
    getLearning: (symbol, horizon) => api.get("/ai/learning/", { params: { symbol, horizon } }),
    preview: (data) => api.post("/ai/preview/", data, { timeout: 75_000 }),

    analyze: (data) =>
        // Gemini may take up to 60 seconds on a full evidence-rich analysis.
        // Leave a small buffer beyond the provider timeout so the browser
        // doesn't abandon a request Athena is still processing.
        api.post("/ai/analyze/", data, { timeout: 75_000 }),

    getSessions: () => api.get("/ai/sessions/"),

    clearSessions: () => api.delete("/ai/sessions/"),

    getSession: (id) => api.get(`/ai/sessions/${id}/`),

    getSignals: () => api.get("/ai/signals/"),

    getTemplates: () => api.get("/ai/templates/"),
};
