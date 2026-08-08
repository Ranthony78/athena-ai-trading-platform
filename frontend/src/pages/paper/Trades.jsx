import { useQuery } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Table, Badge, Spinner } from "../../components/common";
import { paperAPI } from "../../api/paper";
import { formatNumber, formatCurrency, formatDateTime } from "../../utils/formatters";

export default function Trades() {
    const { data: trades, isLoading } = useQuery({
        queryKey: ["paper-trades"],
        queryFn: () => paperAPI.getTrades(),
        select: (res) => res.data.data,
    });

    const columns = [
        { key: "symbol", label: "Symbol" },
        {
            key: "direction",
            label: "Direction",
            render: (val) => (
                <Badge variant={val === "LONG" ? "green" : "red"}>{val}</Badge>
            ),
        },
        { key: "quantity", label: "Qty" },
        {
            key: "entry_price",
            label: "Entry",
            render: (val) => <span className="font-mono">{formatNumber(val)}</span>,
        },
        {
            key: "exit_price",
            label: "Exit",
            render: (val) => <span className="font-mono">{formatNumber(val)}</span>,
        },
        {
            key: "net_pnl",
            label: "Net PnL",
            render: (val) => (
                <span className={`font-mono font-semibold
          ${parseFloat(val) >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {parseFloat(val) >= 0 ? "+" : ""}{formatCurrency(val)}
                </span>
            ),
        },
        {
            key: "exit_time",
            label: "Time",
            render: (val) => formatDateTime(val),
        },
    ];

    return (
        <PageWrapper title="Trade History" subtitle="Completed paper trades">
            <Card padding={false}>
                {isLoading ? (
                    <Spinner />
                ) : (
                    <Table
                        columns={columns}
                        data={trades || []}
                        emptyTitle="No completed trades"
                    />
                )}
            </Card>
        </PageWrapper>
    );
}