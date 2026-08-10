import { TrendingUp, TrendingDown } from "lucide-react";
import { formatNumber, formatPercent, abbreviateNumber } from "../../../utils/formatters";

export default function QuoteCard({ quote, selected, onClick }) {
    const isPos = parseFloat(quote.change_percent) >= 0;

    return (
        <div
            onClick={onClick}
            className={`card cursor-pointer transition-all duration-150
        ${selected
                    ? "border-primary-500 bg-primary-900/10"
                    : "hover:border-dark-600"
                }`}
        >
            <div className="flex items-start justify-between mb-3">
                <p className="text-xs font-semibold text-dark-400 uppercase tracking-wider">
                    {quote.symbol}
                </p>
                <span className={`flex items-center gap-1 text-xs font-medium
          ${isPos ? "text-green-400" : "text-red-400"}`}>
                    {isPos ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                    {formatPercent(quote.change_percent)}
                </span>
            </div>

            <p className="text-2xl font-bold text-dark-50 font-mono mb-3">
                {formatNumber(quote.ltp)}
            </p>

            <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                    <p className="text-dark-600">Open</p>
                    <p className="font-mono text-dark-300">{formatNumber(quote.open)}</p>
                </div>
                <div>
                    <p className="text-dark-600">High</p>
                    <p className="font-mono text-green-400">{formatNumber(quote.high)}</p>
                </div>
                <div>
                    <p className="text-dark-600">Low</p>
                    <p className="font-mono text-red-400">{formatNumber(quote.low)}</p>
                </div>
            </div>

            {quote.volume > 0 && (
                <p className="text-xs text-dark-600 mt-2">
                    Vol: {abbreviateNumber(quote.volume)}
                </p>
            )}
        </div>
    );
}