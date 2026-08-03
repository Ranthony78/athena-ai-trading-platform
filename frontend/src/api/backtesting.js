import api from "./axios";

export const backtestingAPI = {
    getRuns: (params) =>
        api.get("/backtest/runs/", { params }),

    createRun: (data) =>
        api.post("/backtest/runs/", data),

    getRun: (id) =>
        api.get(`/backtest/runs/${id}/`),

    getTrades: (id) =>
        api.get(`/backtest/runs/${id}/trades/`),
};