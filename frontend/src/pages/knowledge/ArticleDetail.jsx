import { useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Brain } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Badge, Spinner } from "../../components/common";
import { knowledgeAPI } from "../../api/knowledge";

export default function ArticleDetail() {
    const { slug } = useParams();

    const { data: article, isLoading, refetch } = useQuery({
        queryKey: ["article", slug],
        queryFn: () => knowledgeAPI.getArticle(slug),
        select: (res) => res.data.data,
    });

    const { mutate: summarize, isPending } = useMutation({
        mutationFn: () => knowledgeAPI.summarizeArticle(slug),
        onSuccess: () => refetch(),
    });

    if (isLoading) return <Spinner />;
    if (!article) return <div className="text-dark-400">Article not found.</div>;

    return (
        <PageWrapper
            title={article.title}
            subtitle={`${article.category} · ${article.source}`}
            actions={
                <Button variant="secondary" size="sm" icon={Brain}
                    loading={isPending} onClick={() => summarize()}>
                    AI Summary
                </Button>
            }
        >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <Card>
                        <div className="prose prose-invert prose-sm max-w-none">
                            <p className="text-dark-200 whitespace-pre-wrap leading-relaxed">
                                {article.content}
                            </p>
                        </div>
                    </Card>
                </div>
                <div className="space-y-4">
                    {article.ai_summary && (
                        <Card title="AI Summary">
                            <p className="text-sm text-dark-300">{article.ai_summary}</p>
                        </Card>
                    )}
                    {article.key_points?.length > 0 && (
                        <Card title="Key Points">
                            <ul className="space-y-2">
                                {article.key_points.map((point, i) => (
                                    <li key={i} className="flex gap-2 text-sm text-dark-300">
                                        <span className="text-primary-400 shrink-0">•</span>
                                        {point}
                                    </li>
                                ))}
                            </ul>
                        </Card>
                    )}
                </div>
            </div>
        </PageWrapper>
    );
}