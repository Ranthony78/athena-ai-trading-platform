import axios from "axios";
import useAuthStore from "../store/authStore";

const api = axios.create({
    baseURL: "/api",
    timeout: 30000,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor — attach JWT token
api.interceptors.request.use(
    (config) => {
        const token = useAuthStore.getState().accessToken;
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// One in-flight refresh shared by every request that hits a 401 at the same
// time. Refresh tokens rotate, so a second parallel refresh would present a
// token that has just been blacklisted and wrongly log the user out.
let refreshPromise = null;

function refreshAccessToken() {
    if (!refreshPromise) {
        const { refreshToken } = useAuthStore.getState();
        refreshPromise = axios
            .post("/api/accounts/token/refresh/", { refresh: refreshToken })
            .then((response) => {
                useAuthStore.getState().setTokens(response.data);
                return response.data.access;
            })
            .finally(() => {
                refreshPromise = null;
            });
    }
    return refreshPromise;
}

function forceLogout() {
    useAuthStore.getState().logout();
    window.location.href = "/login";
}

// Response interceptor — handle auth errors
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config;

        if (error.response?.status === 401 && !original._retry) {
            original._retry = true;

            if (!useAuthStore.getState().refreshToken) {
                forceLogout();
                return Promise.reject(error);
            }

            try {
                const access = await refreshAccessToken();
                original.headers.Authorization = `Bearer ${access}`;
                return api(original);
            } catch {
                forceLogout();
                return Promise.reject(error);
            }
        }

        return Promise.reject(error);
    }
);

export default api;
