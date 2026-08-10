import api from "./axios";

export const strategiesAPI = {
    getStrategies: () =>
        api.get("/strategies/"),

    createStrategy: (data) =>
        api.post("/strategies/", data),

    getStrategy: (id) =>
        api.get(`/strategies/${id}/`),

    updateStrategy: (id, data) =>
        api.put(`/strategies/${id}/`, data),

    deleteStrategy: (id) =>
        api.delete(`/strategies/${id}/`),

    runStrategy: (data) =>
        api.post("/strategies/run/", data),

    runAll: (symbols) =>
        api.post("/strategies/run-all/", { symbols }),

    getSignals: (params) =>
        api.get("/strategies/signals/", { params }),

    getSignalsBySymbol: (symbol) =>
        api.get(`/strategies/signals/${symbol}/`),
};