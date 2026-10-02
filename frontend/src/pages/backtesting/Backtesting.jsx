import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Brain } from "lucide-react";
import { Link } from "react-router-dom";
import { PageWrapper } from "../../components/layout";
import { Card, Table, Badge, Spinner } from "../../components/common";
import { backtestingAPI } from "../../api/backtesting";
import { formatDate, formatNumber } from "../../utils/formatters";

export default function Backtesting() {
    const { data: runs, isLoading } = useQuery({
        queryKey: ["backtest-runs"],
        queryFn: () => backtestingAPI.getRuns(),
        select: (res) => res.data.data,
    });

    const columns = [
        { key: "strategy_name", label: "Archived rule set" },
        { key: "symbol", label: "Symbol" },
        { key: "timeframe", label: "TF" },
        { key: "from_date", label: "From", render: (v) => formatDate(v) },
        { key: "to_date", label: "To", render: (v) => formatDate(v) },
        {
            key: "status",
            label: "Status",
            render: (v) => (
                <Badge variant={v === "COMPLETE" ? "green" : v === "FAILED" ? "red" : "yellow"}>
                    {v}
                </Badge>
            ),
        },
        {
            key: "id",
            label: "Result",
            render: (v, row) =>
                row.status === "COMPLETE" ? (
                    <a href={`/backtest/${v}`}
                        className="text-xs text-primary-400 hover:text-primary-300">
                        View →
                    </a>
                ) : "—",
        },
    ];

    return (
        <PageWrapper
            title="Backtesting Archive"
            subtitle="Review saved historical runs. AI forecast evaluation is available in the AI Workspace."
        >
            <Card className="mb-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <p className="text-sm font-semibold text-dark-100">AI-led research</p>
                        <p className="mt-1 text-xs text-dark-400">
                            New analysis, No Trade decisions, prediction history, and forecast calibration live in one place.
                            The rule-based runs below are preserved for reference.
                        </p>
                    </div>
                    <Link to="/analysis" className="inline-flex shrink-0 items-center gap-2 text-sm font-medium text-primary-400 hover:text-primary-300">
                        <Brain className="h-4 w-4" /> Open AI Workspace <ArrowRight className="h-4 w-4" />
                    </Link>
                </div>
            </Card>
            <Card padding={false}>
                {isLoading ? <Spinner /> : (
                    <Table columns={columns} data={runs || []}
                        emptyTitle="No archived backtests" />
                )}
            </Card>
        </PageWrapper>
    );
}
