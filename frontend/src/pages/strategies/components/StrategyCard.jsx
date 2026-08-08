import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Play } from "lucide-react";
import { Card, Badge, Button, Alert } from "../../../components/common";
import { strategiesAPI } from "../../../api/strategies";

export default function StrategyCard({ strategy }) {
    const [feedback, setFeedback] = useState(null);
    const queryClient = useQueryClient();

    const { mutate: run, isPending } = useMutation({
        mutationFn: () =>
            strategiesAPI.runStrategy({
                strategy_id: strategy.id,
                symbol: "NIFTY",
            }),
        onSuccess: (res) => {
            const result = res.data.data;
            const isTradeable = result.signal !== "NEUTRAL";
            setFeedback({
                type: isTradeable ? "success" : "info",
                message: isTradeable
                    ? `Signal: ${result.signal} (${result.strength}) @ ${result.price}`
                    : `Signal: NEUTRAL @ ${result.price} — not persisted (no tradeable setup).`,
            });
            queryClient.invalidateQueries({ queryKey: ["all-signals"] });
            queryClient.invalidateQueries({ queryKey: ["strategy-signals"] });
        },
        onError: (err) => {
            setFeedback({
                type: "info",
                message: err?.response?.data?.message || "No signal generated. Check candle data.",
            });
        },
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
                onClick={() => {
                    setFeedback(null);
                    run();
                }}
                className="w-full"
            >
                Run on NIFTY
            </Button>

            {feedback && (
                <div className="mt-3">
                    <Alert type={feedback.type} message={feedback.message} />
                </div>
            )}
        </Card>
    );
}