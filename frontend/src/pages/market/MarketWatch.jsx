import { Card, Table, Badge } from "../../components/common";
import { formatNumber, formatRelativeTime } from "../../utils/formatters";

export default function MarketWatch() {
    const columns = [
        { key: "strategy_name", label: "Strategy" },
        { key: "symbol", label: "Symbol" },
        { key: "signal", label: "Signal", render: (val) => (<Badge variant={val === "BUY" ? "green" : val === "SELL" ? "red" : "gray"}>{val}</Badge>) },
        { key: "strength", label: "Strength", render: (val) => (<Badge variant={val === "STRONG" ? "green" : val === "MODERATE" ? "yellow" : "gray"}>{val}</Badge>) },
        { key: "price_at_signal", label: "Price", render: (val) => (<span className="font-mono">{formatNumber(val)}</span>) },
        { key: "signal_time", label: "Time", render: (val) => formatRelativeTime(val) },
    ];

    return (
        <Card title="Strategy Signals" subtitle="Active signals from all strategies" padding={false}>
            <Table columns={columns} data={[]} emptyTitle="No active signals" emptyDescription="Run strategies to generate signals" />
        </Card>
    );
}
