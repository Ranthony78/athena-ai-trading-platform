import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Plus } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Badge, Spinner, EmptyState } from "../../components/common";
import ArticleCard from "./components/ArticleCard";
import { knowledgeAPI } from "../../api/knowledge";

export default function Knowledge() {
    const [search, setSearch] = useState("");
    const [category, setCategory] = useState("");

    const { data: articles, isLoading } = useQuery({
        queryKey: ["articles", category],
        queryFn: () => knowledgeAPI.getArticles({ category }),
        select: (res) => res.data.data,
    });

    const { data: searchResults } = useQuery({
        queryKey: ["knowledge-search", search],
        queryFn: () => knowledgeAPI.search(search),
        select: (res) => res.data.data,
        enabled: search.length >= 2,
    });

    const CATEGORIES = [
        "CONCEPT", "STRATEGY", "INDICATOR",
        "OPTION", "PSYCHOLOGY", "RISK",
    ];

    const displayArticles = search.length >= 2
        ? searchResults?.articles || []
        : articles || [];

    return (
        <PageWrapper
            title="Knowledge Base"
            subtitle="Your trading knowledge library"
            actions={
                <div className="flex gap-2">
                    <a href="/knowledge/rules">
                        <Button variant="secondary" size="sm">Rules</Button>
                    </a>
                    <a href="/knowledge/prompts">
                        <Button variant="secondary" size="sm">Prompts</Button>
                    </a>
                </div>
            }
        >
            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2
                           w-4 h-4 text-dark-500" />
                <input
                    className="input pl-10"
                    placeholder="Search articles, rules, prompts..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            {/* Category Filter */}
            <div className="flex gap-2 flex-wrap">
                <button
                    onClick={() => setCategory("")}
                    className={`badge cursor-pointer ${!category ? "badge-blue" : "badge-gray"}`}
                >
                    All
                </button>
                {CATEGORIES.map((c) => (
                    <button
                        key={c}
                        onClick={() => setCategory(c === category ? "" : c)}
                        className={`badge cursor-pointer ${category === c ? "badge-blue" : "badge-gray"}`}
                    >
                        {c}
                    </button>
                ))}
            </div>

            {/* Articles */}
            {isLoading ? (
                <Spinner />
            ) : !displayArticles.length ? (
                <EmptyState title="No articles found" />
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {displayArticles.map((article) => (
                        <ArticleCard key={article.id || article.slug} article={article} />
                    ))}
                </div>
            )}
        </PageWrapper>
    );
}