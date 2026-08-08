import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { FlaskConical } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Table, Badge, Button, Modal, Spinner } from "../../components/common";
import BacktestForm from "./components/BacktestForm";
import { backtestingAPI } from "../../api/backtesting";
import { formatDate, formatNumber } from "../../utils/formatters";

export default function Backtesting() {
    const [showModal, setShowModal] = useState(false);
    const queryClient = useQueryClient();

    const { data: runs, isLoading } = useQuery({
        queryKey: ["backtest-runs"],
        queryFn: () => backtestingAPI.getRuns(),
        select: (res) => res.data.data,
    });

    const { mutate: create, isPending } = useMutation({
        mutationFn: (data) => backtestingAPI.createRun(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["backtest-runs"] });
            setShowModal(false);
        },
    });

    const columns = [
        { key: "strategy_name", label: "Strategy" },
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
            title="Backtesting"
            subtitle="Test strategies against historical data"
            actions={
                <Button variant="primary" size="sm" icon={FlaskConical}
                    onClick={() => setShowModal(true)}>
                    New Backtest
                </Button>
            }
        >
            <Card padding={false}>
                {isLoading ? <Spinner /> : (
                    <Table columns={columns} data={runs || []}
                        emptyTitle="No backtests yet" />
                )}
            </Card>

            <Modal isOpen={showModal} onClose={() => setShowModal(false)}
                title="New Backtest" size="lg">
                <BacktestForm onSubmit={create} loading={isPending} />
            </Modal>
        </PageWrapper>
    );
}