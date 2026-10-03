import { useQuery } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Spinner, EmptyState, Badge } from "../../components/common";
import { strategiesAPI } from "../../api/strategies";

export default function Strategies() {
    const {
        data: strategies,
        isLoading,
        isError,
    } = useQuery({
        queryKey: ["strategies"],
        queryFn: () => strategiesAPI.getStrategies(),
        select: (res) => res.data.data,
    });

    return (
        <PageWrapper
            title="Strategy Archive"
            subtitle="Previous rule-based templates are preserved here for reference. Athena's AI Workspace is the primary analysis flow."
        >
            <Card className="mb-4">
                <div className="flex items-start gap-3">
                    <Badge variant="gray">Reference only</Badge>
                    <p className="text-sm text-dark-400">
                        These legacy templates are not run by AI analysis and cannot generate new
                        signals from this page.
                    </p>
                </div>
            </Card>

            {isLoading ? (
                <Spinner text="Loading archived strategies..." />
            ) : isError ? (
                <Card>
                    <p className="text-sm text-red-400">
                        Could not load archived strategy details.
                    </p>
                </Card>
            ) : !strategies?.length ? (
                <EmptyState
                    title="No archived strategies"
                    description="New analysis is generated through the AI Workspace."
                />
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {strategies.map((strategy) => (
                        <Card key={strategy.id}>
                            <div className="flex items-start justify-between gap-3 mb-3">
                                <div>
                                    <h2 className="text-sm font-semibold text-dark-100">
                                        {strategy.name}
                                    </h2>
                                    <p className="text-xs text-dark-500 mt-1">
                                        {strategy.strategy_type} · {strategy.timeframe}
                                    </p>
                                </div>
                                <Badge variant={strategy.is_enabled ? "green" : "gray"}>
                                    {strategy.is_enabled ? "Previously active" : "Disabled"}
                                </Badge>
                            </div>
                            {strategy.description && (
                                <p className="text-xs text-dark-400">{strategy.description}</p>
                            )}
                        </Card>
                    ))}
                </div>
            )}
        </PageWrapper>
    );
}
