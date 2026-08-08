import api from "./axios";

export const knowledgeAPI = {
    search: (q) =>
        api.get("/knowledge/search/", { params: { q } }),

    getTags: () =>
        api.get("/knowledge/tags/"),

    getArticles: (params) =>
        api.get("/knowledge/articles/", { params }),

    createArticle: (data) =>
        api.post("/knowledge/articles/", data),

    getArticle: (slug) =>
        api.get(`/knowledge/articles/${slug}/`),

    updateArticle: (slug, data) =>
        api.put(`/knowledge/articles/${slug}/`, data),

    deleteArticle: (slug) =>
        api.delete(`/knowledge/articles/${slug}/`),

    summarizeArticle: (slug) =>
        api.post(`/knowledge/articles/${slug}/summarize/`),

    getBooks: () =>
        api.get("/knowledge/books/"),

    createBook: (data) =>
        api.post("/knowledge/books/", data),

    getRules: (params) =>
        api.get("/knowledge/rules/", { params }),

    createRule: (data) =>
        api.post("/knowledge/rules/", data),

    updateRule: (id, data) =>
        api.put(`/knowledge/rules/${id}/`, data),

    deleteRule: (id) =>
        api.delete(`/knowledge/rules/${id}/`),

    recordRuleBroken: (id) =>
        api.post(`/knowledge/rules/${id}/broken/`),

    getPrompts: (params) =>
        api.get("/knowledge/prompts/", { params }),

    createPrompt: (data) =>
        api.post("/knowledge/prompts/", data),

    usePrompt: (id) =>
        api.post(`/knowledge/prompts/${id}/use/`),
};