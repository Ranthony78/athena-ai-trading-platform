import api from "./axios";

// Strategies are read-only from the UI: create/update/delete and the
// rule-based run endpoints were retired in favour of the AI Workspace
// (the backend answers /strategies/run/ and /run-all/ with 410 Gone).
export const strategiesAPI = {
    getStrategies: () => api.get("/strategies/"),

    getStrategy: (id) => api.get(`/strategies/${id}/`),

    getSignals: (params) => api.get("/strategies/signals/", { params }),

    getSignalsBySymbol: (symbol) => api.get(`/strategies/signals/${symbol}/`),
};
