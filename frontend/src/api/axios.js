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

async function doRefresh(failedAccess) {
    // Another tab may already have refreshed: its new tokens are in
    // localStorage. Re-read them and reuse them instead of spending the old,
    // now-cancelled refresh token.
    await useAuthStore.persist.rehydrate();
    const { accessToken, refreshToken } = useAuthStore.getState();
    if (accessToken && accessToken !== failedAccess) {
        return accessToken;
    }
    const response = await axios.post("/api/accounts/token/refresh/", {
        refresh: refreshToken,
    });
    useAuthStore.getState().setTokens(response.data);
    return response.data.access;
}

function refreshAccessToken(failedAccess) {
    if (!refreshPromise) {
        // The Web Locks API lets only one tab refresh at a time; the others
        // wait and then pick up the result via doRefresh's re-read.
        const run = () => doRefresh(failedAccess);
        refreshPromise = (
            navigator.locks ? navigator.locks.request("athena-token-refresh", run) : run()
        ).finally(() => {
            refreshPromise = null;
        });
    }
    return refreshPromise;
}

function forceLogout() {
    useAuthStore.getState().logout();
    window.location.href = "/login";
}

// The refresh token itself was rejected (expired, cancelled or malformed).
// Anything else - network error, timeout, busy or failing server, rate limit -
// is temporary, and the user stays signed in.
function refreshTokenRejected(error) {
    const status = error?.response?.status;
    return status === 401 || status === 400;
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

            const failedAccess = String(original.headers?.Authorization || "").replace(
                /^Bearer /,
                ""
            );
            try {
                const access = await refreshAccessToken(failedAccess);
                original.headers.Authorization = `Bearer ${access}`;
                return api(original);
            } catch (refreshError) {
                if (refreshTokenRejected(refreshError)) {
                    forceLogout();
                }
                return Promise.reject(error);
            }
        }

        return Promise.reject(error);
    }
);

export default api;
