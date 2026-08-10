import api from "./axios";

export const authAPI = {
    login: (credentials) =>
        api.post("/accounts/login/", credentials),

    logout: (refresh) =>
        api.post("/accounts/logout/", { refresh }),

    profile: () =>
        api.get("/accounts/profile/"),

    refreshToken: (refresh) =>
        api.post("/accounts/token/refresh/", { refresh }),
};