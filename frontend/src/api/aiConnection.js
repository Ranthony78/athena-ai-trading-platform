import api from "./axios";

export const aiConnectionAPI = {
    getStatus: () => api.get("/ai/provider/"),
    testConnection: () => api.post("/ai/provider/", {}),
    saveCredentials: (data) => api.put("/ai/provider/", data),
    removeCredentials: () => api.delete("/ai/provider/"),
};
