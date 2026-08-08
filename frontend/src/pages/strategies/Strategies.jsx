import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Modal, Spinner, EmptyState, Alert } from "../../components/common";
import StrategyCard from "./components/StrategyCard";
import StrategyForm from "./components/StrategyForm";
import { strategiesAPI } from "../../api/strategies";

export default function Strategies() {
    const [showModal, setShowModal] = useState(false);
    const [runFeedback, setRunFeedback] = useState(null);
    const queryClient = useQueryClient();

    const { data: strategies, isLoading } = useQuery({
        queryKey: ["strategies"],
        queryFn: () => strategiesAPI.getStrategies(),
        select: (res) => res.data.data,
    });

    const { mutate: create, isPending } = useMutation({
        mutationFn: (data) => strategiesAPI.createStrategy(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["strategies"] });
            setShowModal(false);
        },
    });

    const { mutate: runAll, isPending: running } = useMutation({
        mutationFn: () => strategiesAPI.runAll(["NIFTY", "BANKNIFTY"]),
        onSuccess: (res) => {
            const results = res.data.data || {};

            // Only BUY/SELL signals get persisted to the database — a
            // NEUTRAL result is a valid evaluation but isn't a tradeable
            // signal, so don't count it as one (matches strategy_engine.py's
            // persist condition: `if persist and result.signal != "NEUTRAL"`).
            const totalSignals = Object.values(results).reduce(
                (sum, signals) =>
                    sum + (signals?.filter((s) => s.signal !== "NEUTRAL").length || 0),
                0
            );
            const totalEvaluated = Object.values(results).reduce(
                (sum, signals) => sum + (signals?.length || 0),
                0
            );

            setRunFeedback({
                type: totalSignals > 0 ? "success" : "info",
                title: totalSignals > 0
                    ? `Run complete: ${totalSignals} signal${totalSignals === 1 ? "" : "s"} generated`
                    : "Run complete: no tradeable signals",
                message: totalSignals > 0
                    ? "Check Strategy Signals for details."
                    : `${totalEvaluated} strateg${totalEvaluated === 1 ? "y" : "ies"} evaluated, all NEUTRAL — nothing persisted.`,
            });

            queryClient.invalidateQueries({ queryKey: ["all-signals"] });
            queryClient.invalidateQueries({ queryKey: ["strategy-signals"] });
        },
        onError: (err) => {
            setRunFeedback({
                type: "error",
                title: "Run failed",
                message: err?.response?.data?.message || "Could not run strategies. Check the backend logs.",
            });
        },
    });

    return (
        <PageWrapper
            title="Strategies"
            subtitle="Manage and run trading strategies"
            actions={
                <div className="flex gap-2">
                    <Button
                        variant="secondary"
                        size="sm"
                        loading={running}
                        onClick={() => {
                            setRunFeedback(null);
                            runAll();
                        }}
                    >
                        Run All
                    </Button>
                    <Button
                        variant="primary"
                        size="sm"
                        icon={Plus}
                        onClick={() => setShowModal(true)}
                    >
                        New Strategy
                    </Button>
                </div>
            }
        >
            {runFeedback && (
                <div className="mb-4">
                    <Alert
                        type={runFeedback.type}
                        title={runFeedback.title}
                        message={runFeedback.message}
                    />
                </div>
            )}

            {isLoading ? (
                <Spinner text="Loading strategies..." />
            ) : !strategies?.length ? (
                <EmptyState
                    title="No strategies yet"
                    description="Create your first trading strategy"
                    action={
                        <Button
                            variant="primary"
                            size="sm"
                            icon={Plus}
                            onClick={() => setShowModal(true)}
                        >
                            Create Strategy
                        </Button>
                    }
                />
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {strategies.map((strategy) => (
                        <StrategyCard key={strategy.id} strategy={strategy} />
                    ))}
                </div>
            )}

            <Modal
                isOpen={showModal}
                onClose={() => setShowModal(false)}
                title="Create Strategy"
            >
                <StrategyForm onSubmit={create} loading={isPending} />
            </Modal>
        </PageWrapper>
    );
}