import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Spinner } from "../../components/common";
import ResultStats from "./components/ResultStats";
import TradeTable from "./components/TradeTable";
import { backtestingAPI } from "../../api/backtesting";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function BacktestResult() {
    const { id } = useParams();

    const { data: run, isLoading } = useQuery({
        queryKey: ["backtest-run", id],
        queryFn: () => backtestingAPI.getRun(id),
        select: (res) => res.data.data,
    });

    const { data: trades } = useQuery({
        queryKey: ["backtest-trades", id],
        queryFn: () => backtestingAPI.getTrades(id),
        select: (res) => res.data.data,
    });

    if (isLoading) return <Spinner text="Loading results..." />;
    if (!run) return <div className="text-dark-400">Run not found.</div>;

    return (
        <PageWrapper
            title={`Backtest: ${run.strategy_name}`}
            subtitle={`${run.symbol} · ${run.timeframe} · ${run.from_date} → ${run.to_date}`}
        >
            {run.result && <ResultStats result={run.result} />}

            {/* Equity Curve */}
            {run.result?.equity_curve?.length > 0 && (
                <Card title="Equity Curve">
                    <ResponsiveContainer width="100%" height={250}>
                        <LineChart data={run.result.equity_curve}>
                            <XAxis dataKey="time" hide />
                            <YAxis domain={["auto", "auto"]} />
                            <Tooltip
                                contentStyle={{
                                    background: "#1e293b",
                                    border: "1px solid #334155",
                                    borderRadius: "8px",
                                }}
                            />
                            <Line
                                type="monotone"
                                dataKey="capital"
                                stroke="#3b82f6"
                                dot={false}
                                strokeWidth={2}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </Card>
            )}

            {/* Trades */}
            <TradeTable trades={trades || []} />
        </PageWrapper>
    );
}