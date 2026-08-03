import { formatCurrency, formatPercent } from "../../../utils/formatters";

export default function PortfolioStats({ portfolio }) {
    if (!portfolio) return null;
    const { account, trades } = portfolio;

    const stats = [
        {
            label: "Balance",
            value: formatCurrency(account.balance),
            color: "text-dark-50",
        },
        {
            label: "Available",
            value: formatCurrency(account.available_balance),
            color: "text-dark-50",
        },
        {
            label: "Today PnL",
            value: formatCurrency(account.today_pnl),
            color: parseFloat(account.today_pnl) >= 0
                ? "text-green-400" : "text-red-400",
        },
        {
            label: "Total PnL",
            value: formatCurrency(account.total_pnl),
            color: parseFloat(account.total_pnl) >= 0
                ? "text-green-400" : "text-red-400",
        },
        {
            label: "Return",
            value: formatPercent(account.total_return_pct),
            color: parseFloat(account.total_return_pct) >= 0
                ? "text-green-400" : "text-red-400",
        },
        {
            label: "Win Rate",
            value: `${account.win_rate}%`,
            color: "text-dark-50",
        },
        {
            label: "Total Trades",
            value: account.total_trades,
            color: "text-dark-50",
        },
        {
            label: "W / L",
            value: `${account.winning_trades} / ${account.losing_trades}`,
            color: "text-dark-50",
        },
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map((stat) => (
                <div key={stat.label} className="card text-center">
                    <p className="stat-label">{stat.label}</p>
                    <p className={`stat-value text-lg ${stat.color}`}>
                        {stat.value}
                    </p>
                </div>
            ))}
        </div>
    );
}