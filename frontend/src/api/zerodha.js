import api from "./axios";

export const zerodhaAPI = {
    getStatus: () =>
        api.get("/zerodha/status/"),

    getConfig: () =>
        api.get("/zerodha/config/"),

    saveConfig: (data) =>
        api.put("/zerodha/config/", data),

    getLoginUrl: () =>
        api.get("/zerodha/login-url/"),

    exchangeToken: (request_token) =>
        api.post("/zerodha/token/", { request_token }),

    logout: () =>
        api.post("/zerodha/logout/"),

    getProfile: () =>
        api.get("/zerodha/profile/"),

    getFunds: () =>
        api.get("/zerodha/funds/"),

    getOrders: () =>
        api.get("/zerodha/orders/"),

    placeOrder: (data) =>
        api.post("/zerodha/orders/", data),

    cancelOrder: (orderId) =>
        api.post(`/zerodha/orders/${orderId}/cancel/`),

    getPositions: () =>
        api.get("/zerodha/positions/"),

    getHoldings: () =>
        api.get("/zerodha/holdings/"),
};