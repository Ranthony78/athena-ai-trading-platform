import { TrendingUp, TrendingDown } from "lucide-react";
import { formatNumber, formatPercent } from "../../../utils/formatters";

// Athena trades Nifty 50 and Bank Nifty weekly options — those two deserve
// visual priority. Everything else (Sensex, Finnifty, Midcpnifty) is
// reference context, not something the platform generates signals for.
const PRIMARY_SYMBOLS = new Set(["NIFTY", "NIFTY50", "BANKNIFTY"]);

function RangeBar({ open, high, low, ltp }) {
    const o = parseFloat(open);
    const h = parseFloat(high);
    const l = parseFloat(low);
    const p = parseFloat(ltp);
    if ([o, h, l, p].some(Number.isNaN) || h === l) return null;

    const pct = Math.min(100, Math.max(0, ((p - l) / (h - l)) * 100));
    const openPct = Math.min(100, Math.max(0, ((o - l) / (h - l)) * 100));

    return (
        <div className="relative h-1 rounded-full bg-dark-800 mt-3">
            <div
                className="absolute top-1/2 -translate-y-1/2 w-px h-2 bg-dark-500"
                style={{ left: `${openPct}%` }}
                title="Open"
            />
            <div
                className={`absolute top-1/2 -translate-y-1/2 w-1.5 h-1.5
          rounded-full ${p >= o ? "bg-green-400" : "bg-red-400"}`}
                style={{ left: `${pct}%` }}
                title="LTP"
            />
        </div>
    );
}

export default function MarketSummaryCard({ quote }) {
    if (!quote) return null;

    const isPositive = parseFloat(quote.change_percent) >= 0;
    const isPrimary = PRIMARY_SYMBOLS.has(quote.symbol?.toUpperCase());

    return (
        <div
            className={`card ${isPrimary
                ? "border-primary-500/40"
                : "opacity-90"
                }`}
        >
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-xs text-dark-500 font-medium uppercase tracking-wider">
                        {quote.symbol}
                        {isPrimary && (
                            <span className="ml-1.5 text-primary-400">•</span>
                        )}
                    </p>
                    <p
                        className={`font-bold text-dark-50 mt-1 font-mono
              ${isPrimary ? "text-2xl" : "text-xl"}`}
                    >
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

            <RangeBar
                open={quote.open}
                high={quote.high}
                low={quote.low}
                ltp={quote.ltp}
            />

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