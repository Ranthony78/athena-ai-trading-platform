import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Table, Badge, Button, Modal, Spinner } from "../../components/common";
import OrderForm from "./components/OrderForm";
import { paperAPI } from "../../api/paper";
import { formatNumber, formatDateTime } from "../../utils/formatters";

export default function Orders() {
    const [showModal, setShowModal] = useState(false);
    const queryClient = useQueryClient();

    const { data: orders, isLoading } = useQuery({
        queryKey: ["paper-orders"],
        queryFn: () => paperAPI.getTodayOrders(),
        select: (res) => res.data.data,
    });

    const { mutate: placeOrder, isPending } = useMutation({
        mutationFn: (data) => paperAPI.placeOrder(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["paper-orders"] });
            queryClient.invalidateQueries({ queryKey: ["portfolio"] });
            setShowModal(false);
        },
    });

    const columns = [
        { key: "symbol", label: "Symbol" },
        {
            key: "transaction_type",
            label: "Type",
            render: (val) => (
                <Badge variant={val === "BUY" ? "green" : "red"}>{val}</Badge>
            ),
        },
        { key: "order_type", label: "Order" },
        { key: "quantity", label: "Qty" },
        {
            key: "price",
            label: "Price",
            render: (val) => <span className="font-mono">{formatNumber(val)}</span>,
        },
        {
            key: "average_price",
            label: "Avg Price",
            render: (val) => <span className="font-mono">{formatNumber(val)}</span>,
        },
        {
            key: "status",
            label: "Status",
            render: (val) => (
                <Badge variant={
                    val === "COMPLETE" ? "green" :
                        val === "CANCELLED" ? "gray" : "yellow"
                }>
                    {val}
                </Badge>
            ),
        },
        {
            key: "order_time",
            label: "Time",
            render: (val) => formatDateTime(val),
        },
    ];

    return (
        <PageWrapper
            title="Orders"
            subtitle="Today's paper trading orders"
            actions={
                <Button
                    variant="primary"
                    size="sm"
                    icon={Plus}
                    onClick={() => setShowModal(true)}
                >
                    Place Order
                </Button>
            }
        >
            <Card padding={false}>
                {isLoading ? (
                    <Spinner />
                ) : (
                    <Table
                        columns={columns}
                        data={orders || []}
                        emptyTitle="No orders today"
                    />
                )}
            </Card>

            <Modal
                isOpen={showModal}
                onClose={() => setShowModal(false)}
                title="Place Paper Order"
            >
                <OrderForm onSubmit={placeOrder} loading={isPending} />
            </Modal>
        </PageWrapper>
    );
}