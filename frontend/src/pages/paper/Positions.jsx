import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { PageWrapper } from "../../components/layout";
import { Card, Table, Badge, Spinner } from "../../components/common";
import { paperAPI } from "../../api/paper";
import { formatNumber, formatCurrency } from "../../utils/formatters";

export default function Positions() {
    const navigate = useNavigate();
    const { data: positions, isLoading } = useQuery({
        queryKey: ["paper-positions"],
        queryFn: () => paperAPI.getPositions(),
        refetchInterval: 10000,
        select: (res) => res.data.data,
    });

    const closePaperPosition = (position) => {
        const params = new URLSearchParams({
            symbol: position.trading_symbol,
            instrument_id: String(position.instrument_id),
            quantity: String(position.quantity),
            transaction_type: "SELL",
        });
        if (position.analysis_session_id) {
            params.set("analysis_session_id", String(position.analysis_session_id));
        }
        navigate(`/paper/orders?${params.toString()}`);
    };

    const columns = [
        { key: "symbol", label: "Symbol" },
        {
            key: "direction",
            label: "Direction",
            render: (val) => <Badge variant={val === "LONG" ? "green" : "red"}>{val}</Badge>,
        },
        { key: "quantity", label: "Qty" },
        {
            key: "average_price",
            label: "Avg Price",
            render: (val) => <span className="font-mono">{formatNumber(val)}</span>,
        },
        {
            key: "last_price",
            label: "LTP",
            render: (val) => <span className="font-mono">{formatNumber(val)}</span>,
        },
        {
            key: "unrealized_pnl",
            label: "Unrealized PnL",
            render: (val) => (
                <span
                    className={`font-mono font-semibold
          ${parseFloat(val) >= 0 ? "text-green-400" : "text-red-400"}`}
                >
                    {formatCurrency(val)}
                </span>
            ),
        },
        {
            key: "pnl_pct",
            label: "PnL %",
            render: (val) => (
                <span className={parseFloat(val) >= 0 ? "text-green-400" : "text-red-400"}>
                    {parseFloat(val) >= 0 ? "+" : ""}
                    {parseFloat(val).toFixed(2)}%
                </span>
            ),
        },
        {
            key: "instrument_id",
            label: "Paper action",
            render: (_, row) =>
                row.option_type ? (
                    <button
                        type="button"
                        className="text-primary-400 hover:text-primary-300"
                        onClick={() => closePaperPosition(row)}
                    >
                        Close paper position
                    </button>
                ) : null,
        },
    ];

    return (
        <PageWrapper title="Positions" subtitle="Open paper trading positions">
            <Card padding={false}>
                {isLoading ? (
                    <Spinner />
                ) : (
                    <Table
                        columns={columns}
                        data={positions || []}
                        emptyTitle="No open positions"
                    />
                )}
            </Card>
        </PageWrapper>
    );
}
