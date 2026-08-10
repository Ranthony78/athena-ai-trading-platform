import api from "./axios";

export const marketAPI = {
    // Instruments
    getInstruments: (params) =>
        api.get("/market/instruments/", { params }),

    searchInstruments: (q) =>
        api.get("/market/instruments/search/", { params: { q } }),

    getInstrument: (symbol) =>
        api.get(`/market/instruments/${symbol}/`),

    // Indices
    getIndices: () =>
        api.get("/market/indices/"),

    // Quotes
    getQuotes: () =>
        api.get("/market/quotes/"),

    getQuote: (symbol) =>
        api.get(`/market/quotes/${symbol}/`),

    getBulkQuotes: (symbols) =>
        api.post("/market/quotes/bulk/", { symbols }),

    // Historical
    getHistorical: (symbol, params) =>
        api.get(`/market/historical/${symbol}/`, { params }),

    // Expiry
    getExpiry: (symbol) =>
        api.get(`/market/expiry/${symbol}/`),

    // Option Chain
    getOptionChain: (symbol) =>
        api.get(`/market/option-chain/${symbol}/`),

    // Session
    getSession: () =>
        api.get("/market/session/"),

    getEngineStatus: () =>
        api.get("/market/engine/status/"),

    // Indicators
    getIndicatorList: () =>
        api.get("/market/indicators/"),

    calculateIndicators: (data) =>
        api.post("/market/indicators/calculate/", data),

    getAnalysisReport: (symbol) => api.get(`/market/report/${symbol}/`),
};