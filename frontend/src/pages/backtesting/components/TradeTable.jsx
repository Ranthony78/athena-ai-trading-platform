import { Card, Table, Badge } from "../../../components/common";
import { formatNumber, formatCurrency, formatDateTime } from "../../../utils/formatters";

export default function TradeTable({ trades = [] }) {
    const columns = [
        {
            key: "direction",
            label: "Dir",
            render: (v) => <Badge variant={v === "LONG" ? "green" : "red"}>{v}</Badge>,
        },
        {
            key: "entry_price", label: "Entry",
            render: (v) => <span className="font-mono">{formatNumber(v)}</span>
        },
        {
            key: "exit_price", label: "Exit",
            render: (v) => <span className="font-mono">{formatNumber(v)}</span>
        },
        {
            key: "net_pnl",
            label: "Net PnL",
            render: (v) => (
                <span className={`font-mono font-semibold
          ${parseFloat(v) >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {parseFloat(v) >= 0 ? "+" : ""}{formatCurrency(v)}
                </span>
            ),
        },
        { key: "exit_reason", label: "Exit Reason" },
        { key: "entry_time", label: "Entry Time", render: (v) => formatDateTime(v) },
    ];

    return (
        <Card title={`Trade Log (${trades.length} trades)`} padding={false}>
            <Table columns={columns} data={trades} emptyTitle="No trades" />
        </Card>
    );
}