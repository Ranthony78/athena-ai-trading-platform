import { Briefcase } from "lucide-react";
import { Card, EmptyState } from "../../../components/common";
import { formatCurrency, formatPercent } from "../../../utils/formatters";

export default function PortfolioCard({ portfolio }) {
    if (!portfolio) {
        return (
            <Card title="Portfolio">
                <EmptyState icon={Briefcase} title="No portfolio data" />
            </Card>
        );
    }

    const { account, positions } = portfolio;
    const pnlPositive = parseFloat(account.today_pnl) >= 0;
    const hasTrades = account.total_trades > 0;

    return (
        <Card title="Paper Portfolio" actions={<a href="/paper" className="text-xs text-primary-400 hover:text-primary-300">View</a>}>
            <div className="space-y-4">
                {/* Today's PnL is the number you actually check mid-session —
                    give it the primary slot instead of the static balance. */}
                <div className="p-3 bg-dark-800 rounded-lg border border-dark-700">
                    <p className="text-xs text-dark-500">Today PnL</p>
                    <p className={`text-2xl font-bold font-mono
            ${pnlPositive ? "text-green-400" : "text-red-400"}`}>
                        {pnlPositive ? "+" : ""}{formatCurrency(account.today_pnl)}
                    </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-dark-800 rounded-lg">
                        <p className="text-xs text-dark-500">Available Balance</p>
                        <p className="text-sm font-bold text-dark-50 font-mono">{formatCurrency(account.available_balance)}</p>
                    </div>
                    <div className="p-3 bg-dark-800 rounded-lg">
                        <p className="text-xs text-dark-500">Total Return</p>
                        <p className={`text-sm font-bold ${parseFloat(account.total_return_pct) >= 0 ? "text-green-400" : "text-red-400"}`}>{formatPercent(account.total_return_pct)}</p>
                    </div>
                    <div className="p-3 bg-dark-800 rounded-lg">
                        <p className="text-xs text-dark-500">Open Positions</p>
                        <p className="text-sm font-bold text-dark-100">{positions.open_count}</p>
                    </div>
                    <div className="p-3 bg-dark-800 rounded-lg">
                        <p className="text-xs text-dark-500">Win Rate</p>
                        <p className="text-sm font-bold text-dark-100">
                            {hasTrades ? `${account.win_rate}%` : "—"}
                        </p>
                        {!hasTrades && (
                            <p className="text-[10px] text-dark-600 mt-0.5">No trades yet</p>
                        )}
                    </div>
                </div>
            </div>
        </Card>
    );
}