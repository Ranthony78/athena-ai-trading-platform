import { useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Brain } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Badge, Spinner } from "../../components/common";
import AIReviewCard from "./components/AIReviewCard";
import { journalAPI } from "../../api/journal";
import { formatDate, formatCurrency } from "../../utils/formatters";

export default function JournalEntry() {
    const { id } = useParams();

    const { data: entry, isLoading, refetch } = useQuery({
        queryKey: ["journal-entry", id],
        queryFn: () => journalAPI.getEntry(id),
        select: (res) => res.data.data,
    });

    const { mutate: getReview, isPending: reviewing } = useMutation({
        mutationFn: () => journalAPI.getAIReview(id),
        onSuccess: () => refetch(),
    });

    if (isLoading) return <Spinner text="Loading entry..." />;
    if (!entry) return <div className="text-dark-400">Entry not found.</div>;

    return (
        <PageWrapper
            title={entry.title}
            subtitle={`${formatDate(entry.date)} · ${entry.session}`}
            actions={
                <Button
                    variant="primary"
                    size="sm"
                    icon={Brain}
                    loading={reviewing}
                    onClick={() => getReview()}
                >
                    Get AI Review
                </Button>
            }
        >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-4">
                    {/* Summary */}
                    <Card title="Session Summary">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {[
                                { label: "Bias", value: entry.market_bias || "—" },
                                { label: "Mood", value: entry.mood || "—" },
                                { label: "Trades", value: entry.trades_taken },
                                { label: "Rating", value: `${entry.rating}/10` },
                            ].map((s) => (
                                <div key={s.label} className="text-center p-3 bg-dark-800 rounded-lg">
                                    <p className="stat-label">{s.label}</p>
                                    <p className="text-sm font-semibold text-dark-100">{s.value}</p>
                                </div>
                            ))}
                        </div>
                    </Card>

                    {/* Notes */}
                    {[
                        { title: "Market Notes", content: entry.market_notes },
                        { title: "What Worked", content: entry.what_worked },
                        { title: "What Didn't Work", content: entry.what_didnt_work },
                        { title: "Lessons Learned", content: entry.lessons_learned },
                        { title: "Tomorrow's Plan", content: entry.tomorrow_plan },
                    ].filter((s) => s.content).map((section) => (
                        <Card key={section.title} title={section.title}>
                            <p className="text-sm text-dark-300 whitespace-pre-wrap">
                                {section.content}
                            </p>
                        </Card>
                    ))}
                </div>

                {/* Sidebar */}
                <div className="space-y-4">
                    {/* PnL */}
                    <Card title="PnL">
                        <div className="text-center py-2">
                            <p className={`text-2xl font-bold font-mono
                ${parseFloat(entry.total_pnl) >= 0
                                    ? "text-green-400" : "text-red-400"}`}>
                                {formatCurrency(entry.total_pnl)}
                            </p>
                            <p className="text-xs text-dark-500 mt-1">
                                {entry.winners}W / {entry.losers}L
                            </p>
                        </div>
                    </Card>

                    {/* AI Review */}
                    {entry.ai_review && (
                        <AIReviewCard review={entry.ai_review} />
                    )}
                </div>
            </div>
        </PageWrapper>
    );
}