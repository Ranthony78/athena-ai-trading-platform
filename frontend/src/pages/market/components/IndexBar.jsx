import { TrendingUp, TrendingDown, Activity } from "lucide-react";
import { formatNumber, formatPercent } from "../../../utils/formatters";
import { getSessionColor } from "../../../utils/helpers";

export default function IndexBar({ quotes = [], session }) {
    return (
        <div className="card p-3">
            <div className="flex items-center gap-6 overflow-x-auto">
                {/* Session */}
                {session && (
                    <div className="flex items-center gap-2 shrink-0">
                        <Activity className="w-4 h-4 text-dark-500" />
                        <span className={`text-xs font-semibold ${getSessionColor(session.session)}`}>
                            {session.session}
                        </span>
                        <span className="text-dark-600 text-xs font-mono">
                            {session.time}
                        </span>
                    </div>
                )}

                {session && quotes.length > 0 && (
                    <div className="w-px h-6 bg-dark-700 shrink-0" />
                )}

                {/* Quotes */}
                {quotes.map((quote) => {
                    const isPos = parseFloat(quote.change_percent) >= 0;
                    return (
                        <div
                            key={quote.symbol}
                            className="flex items-center gap-3 shrink-0"
                        >
                            <span className="text-xs font-medium text-dark-400">
                                {quote.symbol}
                            </span>
                            <span className="text-sm font-bold text-dark-50 font-mono">
                                {formatNumber(quote.ltp)}
                            </span>
                            <span className={`flex items-center gap-1 text-xs font-medium
                ${isPos ? "text-green-400" : "text-red-400"}`}>
                                {isPos ? (
                                    <TrendingUp className="w-3 h-3" />
                                ) : (
                                    <TrendingDown className="w-3 h-3" />
                                )}
                                {formatPercent(quote.change_percent)}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}