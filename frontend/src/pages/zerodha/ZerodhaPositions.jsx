import { useQuery } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Table, Badge, Spinner } from "../../components/common";
import { zerodhaAPI } from "../../api/zerodha";
import { formatNumber, formatCurrency } from "../../utils/formatters";

export default function ZerodhaPositions() {
    const { data: positions, isLoading } = useQuery({
        queryKey: ["zerodha-positions"],
        queryFn: () => zerodhaAPI.getPositions(),
        refetchInterval: 5000,
        select: (res) => {
            const data = res.data.data;
            return [
                ...(data?.day || []),
                ...(data?.net || []),
            ];
        },
    });

    const columns = [
        { key: "tradingsymbol", label: "Symbol" },
        {
            key: "quantity",
            label: "Qty",
            render: (v) => (
                <span className={v > 0 ? "text-green-400" : v < 0 ? "text-red-400" : ""}>
                    {v}
                </span>
            ),
        },
        {
            key: "average_price",
            label: "Avg",
            render: (v) => <span className="font-mono">{formatNumber(v)}</span>,
        },
        {
            key: "last_price",
            label: "LTP",
            render: (v) => <span className="font-mono">{formatNumber(v)}</span>,
        },
        {
            key: "pnl",
            label: "PnL",
            render: (v) => (
                <span className={`font-mono font-semibold
          ${parseFloat(v) >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {formatCurrency(v)}
                </span>
            ),
        },
        { key: "product", label: "Product" },
    ];

    return (
        <PageWrapper title="Zerodha Positions" subtitle="Live broker positions">
            <Card padding={false}>
                {isLoading ? <Spinner /> : (
                    <Table columns={columns} data={positions || []}
                        emptyTitle="No open positions" />
                )}
            </Card>
        </PageWrapper>
    );
}