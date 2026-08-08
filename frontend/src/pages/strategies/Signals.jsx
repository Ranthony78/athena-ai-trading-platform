import { useQuery } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Table, Badge, Spinner } from "../../components/common";
import { strategiesAPI } from "../../api/strategies";
import { formatNumber, formatRelativeTime } from "../../utils/formatters";

export default function Signals() {
    const { data: signals, isLoading } = useQuery({
        queryKey: ["all-signals"],
        queryFn: () => strategiesAPI.getSignals(),
        refetchInterval: 30000,
        select: (res) => res.data.data,
    });

    const columns = [
        { key: "strategy_name", label: "Strategy" },
        { key: "symbol", label: "Symbol" },
        {
            key: "signal",
            label: "Signal",
            render: (val) => (
                <Badge variant={val === "BUY" ? "green" : val === "SELL" ? "red" : "gray"}>
                    {val}
                </Badge>
            ),
        },
        {
            key: "strength",
            label: "Strength",
            render: (val) => (
                <Badge variant={val === "STRONG" ? "green" : val === "MODERATE" ? "yellow" : "gray"}>
                    {val}
                </Badge>
            ),
        },
        {
            key: "price_at_signal",
            label: "Price",
            render: (val) => <span className="font-mono">{formatNumber(val)}</span>,
        },
        {
            key: "signal_time",
            label: "Time",
            render: (val) => formatRelativeTime(val),
        },
    ];

    return (
        <PageWrapper title="Strategy Signals" subtitle="All generated signals">
            <Card padding={false}>
                {isLoading ? (
                    <Spinner />
                ) : (
                    <Table
                        columns={columns}
                        data={signals || []}
                        emptyTitle="No signals yet"
                        emptyDescription="Run strategies to generate signals"
                    />
                )}
            </Card>
        </PageWrapper>
    );
}