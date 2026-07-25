import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Bell } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Table, Badge, Button, Modal, Spinner } from "../../components/common";
import AlertForm from "./components/AlertForm";
import { notificationsAPI } from "../../api/notifications";
import { formatNumber, formatDateTime } from "../../utils/formatters";

export default function Alerts() {
    const [showModal, setShowModal] = useState(false);
    const queryClient = useQueryClient();

    const { data: alerts, isLoading } = useQuery({
        queryKey: ["alerts"],
        queryFn: () => notificationsAPI.getAlerts(),
        select: (res) => res.data.data,
    });

    const { mutate: create, isPending } = useMutation({
        mutationFn: (data) => notificationsAPI.createAlert(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["alerts"] });
            setShowModal(false);
        },
    });

    const { mutate: cancel } = useMutation({
        mutationFn: (id) => notificationsAPI.cancelAlert(id),
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["alerts"] }),
    });

    const columns = [
        { key: "symbol", label: "Symbol" },
        { key: "alert_type", label: "Type" },
        {
            key: "target_value",
            label: "Target",
            render: (v) => <span className="font-mono">{formatNumber(v)}</span>,
        },
        {
            key: "current_value",
            label: "Current",
            render: (v) => <span className="font-mono">{formatNumber(v)}</span>,
        },
        {
            key: "status",
            label: "Status",
            render: (v) => (
                <Badge variant={v === "ACTIVE" ? "green" : v === "TRIGGERED" ? "blue" : "gray"}>
                    {v}
                </Badge>
            ),
        },
        {
            key: "id",
            label: "Action",
            render: (v, row) =>
                row.status === "ACTIVE" ? (
                    <Button variant="ghost" size="sm" onClick={() => cancel(v)}
                        className="text-red-400">
                        Cancel
                    </Button>
                ) : "—",
        },
    ];

    return (
        <PageWrapper
            title="Price Alerts"
            subtitle="Get notified when prices hit your targets"
            actions={
                <Button variant="primary" size="sm" icon={Bell}
                    onClick={() => setShowModal(true)}>
                    New Alert
                </Button>
            }
        >
            <Card padding={false}>
                {isLoading ? <Spinner /> : (
                    <Table columns={columns} data={alerts || []}
                        emptyTitle="No alerts set" />
                )}
            </Card>

            <Modal isOpen={showModal} onClose={() => setShowModal(false)}
                title="Create Price Alert">
                <AlertForm onSubmit={create} loading={isPending} />
            </Modal>
        </PageWrapper>
    );
}