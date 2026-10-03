import api from "./axios";

export const authAPI = {
    login: (credentials) => api.post("/accounts/login/", credentials),

    register: (details) => api.post("/accounts/register/", details),

    googleLogin: (credential) => api.post("/accounts/google/", { credential }),

    getUsers: (params) => api.get("/accounts/users/", { params }),

    setUserActive: (userId, is_active) =>
        api.patch(`/accounts/users/${userId}/status/`, { is_active }),

    sendUserPasswordReset: (userId) => api.post(`/accounts/users/${userId}/password-reset/`),

    confirmPasswordReset: (data) => api.post("/accounts/password-reset/confirm/", data),

    logout: (refresh) => api.post("/accounts/logout/", { refresh }),

    profile: () => api.get("/accounts/profile/"),

    refreshToken: (refresh) => api.post("/accounts/token/refresh/", { refresh }),
};
