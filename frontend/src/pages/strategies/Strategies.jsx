import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Modal, Spinner, EmptyState } from "../../components/common";
import StrategyCard from "./components/StrategyCard";
import StrategyForm from "./components/StrategyForm";
import { strategiesAPI } from "../../api/strategies";

export default function Strategies() {
    const [showModal, setShowModal] = useState(false);
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
                        onClick={() => runAll()}
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