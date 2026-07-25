import { useQuery } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Table, Badge, Spinner } from "../../components/common";
import { zerodhaAPI } from "../../api/zerodha";
import { formatNumber, formatDateTime } from "../../utils/formatters";

export default function ZerodhaOrders() {
    const { data: orders, isLoading } = useQuery({
        queryKey: ["zerodha-orders"],
        queryFn: () => zerodhaAPI.getOrders(),
        refetchInterval: 10000,
        select: (res) => res.data.data,
    });

    const columns = [
        { key: "tradingsymbol", label: "Symbol" },
        {
            key: "transaction_type",
            label: "Type",
            render: (v) => (
                <Badge variant={v === "BUY" ? "green" : "red"}>{v}</Badge>
            ),
        },
        { key: "order_type", label: "Order" },
        { key: "quantity", label: "Qty" },
        {
            key: "price",
            label: "Price",
            render: (v) => <span className="font-mono">{formatNumber(v)}</span>,
        },
        {
            key: "average_price",
            label: "Avg",
            render: (v) => <span className="font-mono">{formatNumber(v)}</span>,
        },
        {
            key: "status",
            label: "Status",
            render: (v) => (
                <Badge variant={v === "COMPLETE" ? "green" : v === "CANCELLED" ? "gray" : "yellow"}>
                    {v}
                </Badge>
            ),
        },
        {
            key: "order_timestamp",
            label: "Time",
            render: (v) => formatDateTime(v),
        },
    ];

    return (
        <PageWrapper title="Zerodha Orders" subtitle="Live broker orders">
            <Card padding={false}>
                {isLoading ? <Spinner /> : (
                    <Table columns={columns} data={orders || []}
                        emptyTitle="No orders today" />
                )}
            </Card>
        </PageWrapper>
    );
}