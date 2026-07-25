import { formatCurrency, formatPercent } from "../../../utils/formatters";

export default function ResultStats({ result }) {
    if (!result) return null;

    const stats = [
        { label: "Total Trades", value: result.total_trades },
        { label: "Win Rate", value: `${result.win_rate}%` },
        {
            label: "Total Return", value: formatPercent(result.total_return_pct),
            color: parseFloat(result.total_return_pct) >= 0 ? "text-green-400" : "text-red-400"
        },
        {
            label: "Net PnL", value: formatCurrency(result.total_net_pnl),
            color: parseFloat(result.total_net_pnl) >= 0 ? "text-green-400" : "text-red-400"
        },
        { label: "Max Drawdown", value: `${result.max_drawdown_pct}%`, color: "text-red-400" },
        { label: "Sharpe Ratio", value: result.sharpe_ratio },
        { label: "Profit Factor", value: result.profit_factor },
        { label: "Expectancy", value: formatCurrency(result.expectancy) },
        { label: "Avg Win", value: formatCurrency(result.avg_win), color: "text-green-400" },
        { label: "Avg Loss", value: formatCurrency(result.avg_loss), color: "text-red-400" },
        { label: "Max Consec Wins", value: result.consecutive_wins },
        { label: "Max Consec Losses", value: result.consecutive_losses },
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {stats.map((s) => (
                <div key={s.label} className="card text-center">
                    <p className="stat-label text-[10px]">{s.label}</p>
                    <p className={`text-sm font-bold font-mono ${s.color || "text-dark-50"}`}>
                        {s.value}
                    </p>
                </div>
            ))}
        </div>
    );
}