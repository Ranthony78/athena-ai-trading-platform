import api from "./axios";

export const marketAPI = {
    // Instruments
    getInstruments: (params) => api.get("/market/instruments/", { params }),

    searchInstruments: (q) => api.get("/market/instruments/search/", { params: { q } }),

    getInstrument: (symbol) => api.get(`/market/instruments/${symbol}/`),

    // Indices
    getIndices: () => api.get("/market/indices/"),

    // Quotes
    getQuotes: () => api.get("/market/quotes/"),

    getQuote: (symbol) => api.get(`/market/quotes/${symbol}/`),

    getBulkQuotes: (symbols) => api.post("/market/quotes/bulk/", { symbols }),

    // Historical
    getHistorical: (symbol, params) => api.get(`/market/historical/${symbol}/`, { params }),

    getFuturesActivity: (symbol) => api.get(`/market/futures/${symbol}/activity/`),

    // Expiry
    getExpiry: (symbol) => api.get(`/market/expiry/${symbol}/`),

    // Option Chain
    getOptionChain: (symbol, params) => api.get(`/market/option-chain/${symbol}/`, { params }),

    getOptionChainSummary: (symbol, params) =>
        api.get(`/market/option-chain/${symbol}/summary/`, { params }),

    getMarketRead: (symbol) => api.get(`/market/read/${symbol}/`),

    // Session
    getSession: () => api.get("/market/session/"),

    getEngineStatus: () => api.get("/market/engine/status/"),

    // Indicators
    getIndicatorList: () => api.get("/market/indicators/"),

    calculateIndicators: (data) => api.post("/market/indicators/calculate/", data),

    getAnalysisReport: (symbol) => api.get(`/market/report/${symbol}/`),

    getProfitProbability: (symbol, params) =>
        api.get(`/market/profit-probability/${symbol}/`, { params }),

    getOptionsEngine: (symbol, params) => api.get(`/market/options-engine/${symbol}/`, { params }),
};
