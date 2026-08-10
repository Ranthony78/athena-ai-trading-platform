import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, Badge } from "../../../components/common";
import { formatNumber } from "../../../utils/formatters";

function ProbabilityCard({ probability }) {
    if (!probability || probability.upside_pct == null) {
        return (
            <Card title="Intraday Probability">
                <p className="text-sm text-dark-600">
                    Unavailable — needs a real historical base rate (Section 3 was NA for this analysis).
                </p>
            </Card>
        );
    }
    const bars = [
        { label: "Upward", value: probability.upside_pct, color: "text-green-400 border-green-500/40" },
        { label: "Downward", value: probability.downside_pct, color: "text-red-400 border-red-500/40" },
        { label: "Sideways", value: probability.sideways_pct, color: "text-dark-300 border-dark-600" },
    ];
    return (
        <Card title="Intraday Probability" subtitle="Anchored to real historical base rate — see basis below">
            <div className="grid grid-cols-3 gap-3">
                {bars.map((b) => (
                    <div key={b.label} className={`p-3 rounded-lg border text-center ${b.color}`}>
                        <p className="text-2xl font-bold font-mono">{b.value ?? "NA"}%</p>
                        <p className="text-xs text-dark-500 mt-1">{b.label}</p>
                    </div>
                ))}
            </div>
            {probability.basis && (
                <p className="text-xs text-dark-500 mt-3">{probability.basis}</p>
            )}
        </Card>
    );
}

function SentimentCard({ sentiment }) {
    if (!sentiment || !sentiment.classification) {
        return (
            <Card title="Market Sentiment">
                <p className="text-sm text-dark-600">
                    Unavailable — needs VIX, breadth, or news data (Sections 1/4/5 were NA for this analysis).
                </p>
            </Card>
        );
    }
    const variant =
        sentiment.classification?.toLowerCase().includes("bull") ? "green" :
            sentiment.classification?.toLowerCase().includes("bear") ? "red" : "gray";
    return (
        <Card title="Market Sentiment">
            <div className="flex items-center justify-between mb-3">
                <Badge variant={variant}>{sentiment.classification}</Badge>
                {sentiment.confidence_pct != null && (
                    <span className="text-sm font-mono text-dark-300">{sentiment.confidence_pct}% confidence</span>
                )}
            </div>
            {sentiment.key_reasons?.length > 0 && (
                <ul className="text-sm text-dark-300 space-y-1 mb-3">
                    {sentiment.key_reasons.map((r, i) => (
                        <li key={i}>• {r}</li>
                    ))}
                </ul>
            )}
            {sentiment.basis && (
                <p className="text-xs text-dark-500">{sentiment.basis}</p>
            )}
        </Card>
    );
}

function OptionComparisonCard({ comparison }) {
    if (!comparison || !comparison.stronger_side) {
        return (
            <Card title="ATM Option Comparison">
                <p className="text-sm text-dark-600">
                    ITM probability comparison unavailable — needs live option
                    Greeks, which need a live market quote. The real ATM strike
                    and expiry are still shown in the "ATM Option Analysis" card
                    further down this page.
                </p>
            </Card>
        );
    }
    return (
        <Card title="ATM Option Comparison" subtitle="ITM probability approximated from real option delta">
            <div className="grid grid-cols-2 gap-3">
                <div className={`p-3 rounded-lg border text-center ${comparison.stronger_side === "CALL" ? "border-green-500/40 bg-green-500/5" : "border-dark-700"}`}>
                    <p className="text-xs text-dark-500 mb-1">CALL</p>
                    <p className="text-xl font-bold font-mono text-green-400">
                        {comparison.call_itm_probability_pct ?? "NA"}%
                    </p>
                    {comparison.stronger_side === "CALL" && (
                        <Badge variant="green" className="mt-2">Stronger side</Badge>
                    )}
                </div>
                <div className={`p-3 rounded-lg border text-center ${comparison.stronger_side === "PUT" ? "border-red-500/40 bg-red-500/5" : "border-dark-700"}`}>
                    <p className="text-xs text-dark-500 mb-1">PUT</p>
                    <p className="text-xl font-bold font-mono text-red-400">
                        {comparison.put_itm_probability_pct ?? "NA"}%
                    </p>
                    {comparison.stronger_side === "PUT" && (
                        <Badge variant="red" className="mt-2">Stronger side</Badge>
                    )}
                </div>
            </div>
            {comparison.basis && (
                <p className="text-xs text-dark-500 mt-3">{comparison.basis}</p>
            )}
        </Card>
    );
}

function PriceExpectationCard({ expectation }) {
    if (!expectation || expectation.nearest_support == null) {
        return (
            <Card title="Price Expectation">
                <p className="text-sm text-dark-600">
                    Unavailable — needs CPR/Pivot/ATR data for this analysis.
                </p>
            </Card>
        );
    }
    const rows = [
        ["Nearest Support", expectation.nearest_support],
        ["Nearest Resistance", expectation.nearest_resistance],
        ["Expected Range Low", expectation.expected_range_low],
        ["Expected Range High", expectation.expected_range_high],
    ];
    return (
        <Card title="Price Expectation">
            <div className="space-y-2">
                {rows.map(([label, value]) => (
                    <div key={label} className="flex justify-between text-sm">
                        <span className="text-dark-500">{label}</span>
                        <span className="font-mono text-dark-200">{formatNumber(value) ?? "NA"}</span>
                    </div>
                ))}
            </div>
            {expectation.basis && (
                <p className="text-xs text-dark-500 mt-3">{expectation.basis}</p>
            )}
        </Card>
    );
}

function SessionStructureCard({ structure }) {
    if (!structure || structure.length === 0) {
        return (
            <Card title="Today's Realized Session Structure">
                <p className="text-sm text-dark-600">
                    Unavailable — needs live intraday candle data.
                </p>
            </Card>
        );
    }

    const referenceDate = structure.find((b) => b.reference_date)?.reference_date;

    return (
        <Card
            title="Today's Realized Session Structure"
            subtitle={
                referenceDate
                    ? `Today hasn't started — showing ${referenceDate} for reference`
                    : "What actually happened per window — not a prediction"
            }
        >
            {referenceDate && (
                <div className="mb-3 px-3 py-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <p className="text-xs text-yellow-400">
                        Market hasn't opened today yet. The blocks below are from the
                        most recent completed session ({referenceDate}), not today.
                    </p>
                </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {structure.map((b) => {
                    if (b.status === "NOT_STARTED") {
                        return (
                            <div key={b.window} className="p-3 bg-dark-800 rounded-lg opacity-50">
                                <p className="text-xs text-dark-500 mb-1">{b.window}</p>
                                <p className="text-sm text-dark-600">Not started yet</p>
                            </div>
                        );
                    }
                    if (b.status === "NO_DATA") {
                        return (
                            <div key={b.window} className="p-3 bg-dark-800 rounded-lg">
                                <p className="text-xs text-dark-500 mb-1">{b.window}</p>
                                <p className="text-sm text-dark-600">No candle data</p>
                            </div>
                        );
                    }
                    const Icon = b.direction === "Up" ? TrendingUp : b.direction === "Down" ? TrendingDown : Minus;
                    const color = b.direction === "Up" ? "text-green-400" : b.direction === "Down" ? "text-red-400" : "text-dark-400";
                    return (
                        <div key={b.window} className="p-3 bg-dark-800 rounded-lg">
                            <div className="flex items-center justify-between mb-1">
                                <p className="text-xs text-dark-500">{b.window}</p>
                                {b.status === "IN_PROGRESS" && (
                                    <Badge variant="gray" className="text-[10px]">In progress</Badge>
                                )}
                            </div>
                            <div className="flex items-center gap-1">
                                <Icon className={`w-3.5 h-3.5 ${color}`} />
                                <span className={`text-sm font-mono ${color}`}>
                                    {b.move_pts > 0 ? "+" : ""}{b.move_pts} pts
                                </span>
                            </div>
                            <p className="text-xs text-dark-600 mt-1">Range: {b.range_pts} pts</p>
                        </div>
                    );
                })}
            </div>
        </Card>
    );
}

export default function AIInsightsPanel({ result }) {
    if (!result) return null;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ProbabilityCard probability={result.probability} />
            <SentimentCard sentiment={result.sentiment} />
            <OptionComparisonCard comparison={result.option_comparison} />
            <PriceExpectationCard expectation={result.price_expectation} />
            <div className="lg:col-span-2">
                <SessionStructureCard structure={result.session_structure} />
            </div>
        </div>
    );
}