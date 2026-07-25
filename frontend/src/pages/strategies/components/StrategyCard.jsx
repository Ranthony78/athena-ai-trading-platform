import { useMutation } from "@tanstack/react-query";
import { Play } from "lucide-react";
import { Card, Badge, Button } from "../../../components/common";
import { strategiesAPI } from "../../../api/strategies";

export default function StrategyCard({ strategy }) {
    const { mutate: run, isPending } = useMutation({
        mutationFn: () =>
            strategiesAPI.runStrategy({
                strategy_id: strategy.id,
                symbol: "NIFTY",
            }),
    });

    return (
        <Card>
            <div className="flex items-start justify-between mb-3">
                <div>
                    <h3 className="text-sm font-semibold text-dark-100">
                        {strategy.name}
                    </h3>
                    <p className="text-xs text-dark-500 mt-0.5">
                        {strategy.strategy_type} · {strategy.timeframe}
                    </p>
                </div>
                <Badge variant={strategy.is_enabled ? "green" : "gray"}>
                    {strategy.is_enabled ? "Active" : "Disabled"}
                </Badge>
            </div>

            {strategy.description && (
                <p className="text-xs text-dark-400 mb-3">
                    {strategy.description}
                </p>
            )}

            <Button
                variant="secondary"
                size="sm"
                icon={Play}
                loading={isPending}
                onClick={() => run()}
                className="w-full"
            >
                Run on NIFTY
            </Button>
        </Card>
    );
}