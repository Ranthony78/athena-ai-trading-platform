import { TrendingUp, TrendingDown } from "lucide-react";
import { formatNumber, formatPercent } from "../../../utils/formatters";

export default function MarketSummaryCard({ quote }) {
    if (!quote) return null;

    const isPositive = parseFloat(quote.change_percent) >= 0;

    return (
        <div className="card">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-xs text-dark-500 font-medium uppercase tracking-wider">
                        {quote.symbol}
                    </p>
                    <p className="text-xl font-bold text-dark-50 mt-1 font-mono">
                        {formatNumber(quote.ltp)}
                    </p>
                </div>
                <div
                    className={`flex items-center gap-1 text-sm font-medium
            ${isPositive ? "text-green-400" : "text-red-400"}`}
                >
                    {isPositive ? (
                        <TrendingUp className="w-4 h-4" />
                    ) : (
                        <TrendingDown className="w-4 h-4" />
                    )}
                    {formatPercent(quote.change_percent)}
                </div>
            </div>

            <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-dark-800">
                <div>
                    <p className="text-xs text-dark-600">Open</p>
                    <p className="text-xs font-mono text-dark-300">
                        {formatNumber(quote.open)}
                    </p>
                </div>
                <div>
                    <p className="text-xs text-dark-600">High</p>
                    <p className="text-xs font-mono text-green-400">
                        {formatNumber(quote.high)}
                    </p>
                </div>
                <div>
                    <p className="text-xs text-dark-600">Low</p>
                    <p className="text-xs font-mono text-red-400">
                        {formatNumber(quote.low)}
                    </p>
                </div>
            </div>
        </div>
    );
}