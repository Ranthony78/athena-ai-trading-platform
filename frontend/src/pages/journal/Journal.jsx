import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, BookOpen } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Modal, Spinner, EmptyState, Badge } from "../../components/common";
import EntryForm from "./components/EntryForm";
import { journalAPI } from "../../api/journal";
import { formatDate, formatCurrency } from "../../utils/formatters";

export default function Journal() {
    const [showModal, setShowModal] = useState(false);
    const queryClient = useQueryClient();

    const { data: entries, isLoading } = useQuery({
        queryKey: ["journal-entries"],
        queryFn: () => journalAPI.getEntries(),
        select: (res) => res.data.data,
    });

    const { data: stats } = useQuery({
        queryKey: ["journal-stats"],
        queryFn: () => journalAPI.getStats(),
        select: (res) => res.data.data,
    });

    const { mutate: create, isPending } = useMutation({
        mutationFn: (data) => journalAPI.createEntry(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["journal-entries"] });
            setShowModal(false);
        },
    });

    return (
        <PageWrapper
            title="Trading Journal"
            subtitle="Track your trades and learnings"
            actions={
                <div className="flex gap-2">
                    <a href="/journal/lessons">
                        <Button variant="secondary" size="sm">Lessons</Button>
                    </a>
                    <Button
                        variant="primary"
                        size="sm"
                        icon={Plus}
                        onClick={() => setShowModal(true)}
                    >
                        New Entry
                    </Button>
                </div>
            }
        >
            {/* Stats */}
            {stats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                        { label: "Total Entries", value: stats.total_entries },
                        { label: "Avg Rating", value: `${stats.avg_rating}/10` },
                        { label: "Total PnL", value: formatCurrency(stats.total_pnl) },
                        { label: "Total Trades", value: stats.total_trades },
                    ].map((s) => (
                        <div key={s.label} className="card text-center">
                            <p className="stat-label">{s.label}</p>
                            <p className="stat-value text-lg">{s.value}</p>
                        </div>
                    ))}
                </div>
            )}

            {/* Entries */}
            {isLoading ? (
                <Spinner />
            ) : !entries?.length ? (
                <EmptyState
                    icon={BookOpen}
                    title="No journal entries"
                    description="Start documenting your trading journey"
                    action={
                        <Button
                            variant="primary"
                            size="sm"
                            icon={Plus}
                            onClick={() => setShowModal(true)}
                        >
                            Write First Entry
                        </Button>
                    }
                />
            ) : (
                <div className="space-y-3">
                    {entries.map((entry) => (
                        <a key={entry.id} href={`/journal/${entry.id}`}>
                            <Card className="hover:border-dark-600 cursor-pointer
                               transition-colors">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="text-sm font-semibold text-dark-100">
                                            {entry.title}
                                        </p>
                                        <p className="text-xs text-dark-500 mt-1">
                                            {formatDate(entry.date)} · {entry.session}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {entry.market_bias && (
                                            <Badge variant={
                                                entry.market_bias === "BULLISH" ? "green" :
                                                    entry.market_bias === "BEARISH" ? "red" : "gray"
                                            }>
                                                {entry.market_bias}
                                            </Badge>
                                        )}
                                        <span className="text-xs text-dark-500">
                                            ⭐ {entry.rating}/10
                                        </span>
                                        <span className={`text-xs font-mono font-semibold
                      ${parseFloat(entry.total_pnl) >= 0
                                                ? "text-green-400" : "text-red-400"}`}>
                                            {formatCurrency(entry.total_pnl)}
                                        </span>
                                    </div>
                                </div>
                            </Card>
                        </a>
                    ))}
                </div>
            )}

            <Modal
                isOpen={showModal}
                onClose={() => setShowModal(false)}
                title="New Journal Entry"
                size="lg"
            >
                <EntryForm onSubmit={create} loading={isPending} />
            </Modal>
        </PageWrapper>
    );
}