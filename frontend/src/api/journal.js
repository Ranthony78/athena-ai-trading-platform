import api from "./axios";

export const journalAPI = {
    getEntries: (params) =>
        api.get("/journal/entries/", { params }),

    createEntry: (data) =>
        api.post("/journal/entries/", data),

    getEntry: (id) =>
        api.get(`/journal/entries/${id}/`),

    updateEntry: (id, data) =>
        api.put(`/journal/entries/${id}/`, data),

    deleteEntry: (id) =>
        api.delete(`/journal/entries/${id}/`),

    getAIReview: (id) =>
        api.post(`/journal/entries/${id}/review/`),

    getTradeNotes: (id) =>
        api.get(`/journal/entries/${id}/notes/`),

    addTradeNote: (id, data) =>
        api.post(`/journal/entries/${id}/notes/`, data),

    getStats: () =>
        api.get("/journal/stats/"),

    getMistakes: () =>
        api.get("/journal/mistakes/"),

    getLessons: (params) =>
        api.get("/journal/lessons/", { params }),

    addLesson: (data) =>
        api.post("/journal/lessons/", data),

    reinforceLesson: (id) =>
        api.post(`/journal/lessons/${id}/reinforce/`),

    getRules: () =>
        api.get("/journal/rules/"),
};