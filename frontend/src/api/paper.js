import api from "./axios";

export const paperAPI = {
    getPortfolio: () =>
        api.get("/paper/portfolio/"),

    resetPortfolio: () =>
        api.post("/paper/portfolio/reset/"),

    getOrders: (params) =>
        api.get("/paper/orders/", { params }),

    placeOrder: (data) =>
        api.post("/paper/orders/", data),

    getTodayOrders: () =>
        api.get("/paper/orders/today/"),

    cancelOrder: (id) =>
        api.post(`/paper/orders/${id}/cancel/`),

    getPositions: () =>
        api.get("/paper/positions/"),

    getTrades: (params) =>
        api.get("/paper/trades/", { params }),

    getTodayTrades: () =>
        api.get("/paper/trades/today/"),
};