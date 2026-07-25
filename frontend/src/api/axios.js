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

// Response interceptor — handle auth errors
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config;

        if (error.response?.status === 401 && !original._retry) {
            original._retry = true;

            try {
                const refreshToken = useAuthStore.getState().refreshToken;

                if (!refreshToken) {
                    useAuthStore.getState().logout();
                    window.location.href = "/login";
                    return Promise.reject(error);
                }

                const response = await axios.post("/api/accounts/token/refresh/", {
                    refresh: refreshToken,
                });

                const { access } = response.data;
                useAuthStore.getState().setAccessToken(access);
                original.headers.Authorization = `Bearer ${access}`;

                return api(original);
            } catch {
                useAuthStore.getState().logout();
                window.location.href = "/login";
                return Promise.reject(error);
            }
        }

        return Promise.reject(error);
    }
);

export default api;