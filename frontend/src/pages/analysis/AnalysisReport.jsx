import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { RefreshCw, TrendingUp, TrendingDown, Minus, AlertTriangle, Sparkles } from "lucide-react";
import {
    LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { PageWrapper } from "../../components/layout";
import { Card, Badge, Select, Spinner, EmptyState, Button } from "../../components/common";
import { marketAPI } from "../../api/market";
import { analysisAPI } from "../../api/analysis";
import SignalCard from "./components/SignalCard";
import AIInsightsPanel from "./components/AIInsightsPanel";
import AIResponseView from "./components/AIResponseView";

const SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"];
const TIMEFRAMES = [
    { value: "5m", label: "5 Min" },
    { value: "15m", label: "15 Min" },
    { value: "30m", label: "30 Min" },
    { value: "1h", label: "1 Hour" },
];

const TREND_CONFIG = {
    Bullish: { variant: "green", icon: TrendingUp },
    Bearish: { variant: "red", icon: TrendingDown },
    Neutral: { variant: "gray", icon: Minus },
};

// Same mapping used on the main AI Analysis page — kept local here
// rather than shared, to avoid touching that already-working file.
function friendlyErrorMessage(rawError) {
    if (!rawError) return null;
    const lower = rawError.toLowerCase();
    if (lower.includes("credit balance is too low")) {
        return "Your Anthropic API account has no usable credit balance. Add credits or claim a trial credit at console.anthropic.com, then try again.";
    }
    if (lower.includes("anthropic_api_key not set")) {
        return "No Anthropic API key is configured on the backend. Add ANTHROPIC_API_KEY to your .env file and restart the server.";
    }
    if (lower.includes("401") || lower.includes("authentication")) {
        return "The Anthropic API rejected the request as unauthenticated. Check that your API key is valid.";
    }
    if (lower.includes("rate limit") || lower.includes("429")) {
        return "The Anthropic API rate limit was hit. Wait a moment and try again.";
    }
    if (lower.includes("live data not available") || lower.includes("no candle data")) {
        return "No market data is available for this symbol yet, so no analysis could be run.";
    }
    return rawError;
}

function StatBlock({ label, value, mono = true }) {
    return (
        <div>
            <p className="text-xs text-dark-500">{label}</p>
            <p className={`text-sm font-medium text-dark-100 ${mono ? "font-mono" : ""}`}>
                {value ?? "NA"}
            </p>
        </div>
    );
}

function TrendRow({ label, data }) {
    if (!data) {
        return (
            <div className="flex items-center justify-between py-2 border-b border-dark-800 last:border-0">
                <span className="text-sm text-dark-400">{label}</span>
                <span className="text-xs text-dark-600">No data</span>
            </div>
        );
    }
    const config = TREND_CONFIG[data.trend] || TREND_CONFIG.Neutral;
    const Icon = config.icon;
    return (
        <div className="flex items-center justify-between py-2 border-b border-dark-800 last:border-0">
            <span className="text-sm text-dark-300">{label}</span>
            <div className="flex items-center gap-4">
                <span className="text-xs text-dark-500 font-mono">RSI {data.rsi_14}</span>
                <Badge variant={config.variant}>
                    <Icon className="w-3 h-3 inline mr-1" />
                    {data.trend}
                </Badge>
            </div>
        </div>
    );
}

function OptionSideCard({ label, data, accent }) {
    if (!data) {
        return (
            <Card className={`border-l-2 border-${accent}-500/40`}>
                <p className="text-xs text-dark-500">{label}</p>
                <p className="text-sm text-dark-600 mt-2">No data available</p>
            </Card>
        );
    }
    return (
        <Card className={`border-l-2 border-${accent}-500/40`}>
            <p className={`text-xs font-medium text-${accent}-400 uppercase tracking-wide`}>
                {label}
            </p>
            <p className="text-xl font-bold text-dark-50 font-mono mt-1">
                ₹{data.ltp}
            </p>
            <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
                <div>
                    <p className="text-dark-600">OI</p>
                    <p className="text-dark-300 font-mono">{data.oi?.toLocaleString()}</p>
                </div>
                <div>
                    <p className="text-dark-600">IV</p>
                    <p className="text-dark-300 font-mono">{data.iv}%</p>
                </div>
                <div>
                    <p className="text-dark-600">Delta</p>
                    <p className="text-dark-300 font-mono">{data.delta}</p>
                </div>
                <div>
                    <p className="text-dark-600">Theta</p>
                    <p className="text-dark-300 font-mono">{data.theta}</p>
                </div>
            </div>
        </Card>
    );
}

function AIAnalysisSection({ symbol, timeframe }) {
    const [aiResult, setAiResult] = useState(null);

    // Symbol/timeframe changed — the previous AI result no longer applies
    // to what's on screen, so clear it rather than showing a stale signal.
    useEffect(() => {
        setAiResult(null);
    }, [symbol, timeframe]);

    const { mutate: runAI, isPending } = useMutation({
        mutationFn: () => analysisAPI.analyze({ symbol, timeframe, session_type: "MARKET_ANALYSIS", persist: true }),
        onSuccess: (res) => setAiResult(res.data.data),
    });

    const hasError = Boolean(aiResult?.error);

    return (
        <Card
            title="AI Suggestion"
            subtitle="Real AI reasoning + a specific contract to consider — uses your Claude connection, generated on demand"
            actions={
                <Button
                    variant="primary"
                    size="sm"
                    icon={Sparkles}
                    loading={isPending}
                    onClick={() => {
                        setAiResult(null);
                        runAI();
                    }}
                >
                    {aiResult ? "Re-run AI Analysis" : "Get AI Analysis"}
                </Button>
            }
        >
            {!aiResult ? (
                <div className="flex flex-col items-center justify-center py-10 text-center">
                    <p className="text-dark-400 text-sm">No AI suggestion yet for {symbol}</p>
                    <p className="text-dark-600 text-xs mt-1">
                        The snapshot below is already loaded — click "Get AI Analysis" for a signal and suggested contract
                    </p>
                </div>
            ) : hasError ? (
                <div className="flex items-start gap-3 p-1">
                    <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                    <div>
                        <p className="text-sm font-medium text-red-400">Analysis failed</p>
                        <p className="text-sm text-dark-300 mt-1">{friendlyErrorMessage(aiResult.error)}</p>
                    </div>
                </div>
            ) : (
                <div className="space-y-4">
                    <SignalCard result={aiResult} />
                    <AIInsightsPanel result={aiResult} />
                    <AIResponseView response={aiResult.reasoning} />
                </div>
            )}
        </Card>
    );
}

export default function AnalysisReport() {
    const [symbol, setSymbol] = useState("NIFTY");
    const [timeframe, setTimeframe] = useState("15m");

    const { data: report, isLoading, isFetching, refetch } = useQuery({
        queryKey: ["analysis-report", symbol],
        queryFn: () => marketAPI.getAnalysisReport(symbol),
        select: (res) => res.data.data,
    });

    const spot = report?.spot;
    const changePositive = spot && parseFloat(spot.change) >= 0;
    const sr = report?.support_resistance;
    const options = report?.options;
    const lastAnalysis = report?.last_analysis;

    return (
        <PageWrapper
            title="AI Analysis"
            subtitle="Pick a symbol — the snapshot loads automatically, then run AI analysis for a signal and suggested contract"
            actions={
                <div className="flex items-center gap-3">
                    <a
                        href="/analysis/history"
                        className="text-xs text-primary-400 hover:text-primary-300"
                    >
                        View History
                    </a>
                    <Select
                        value={symbol}
                        onChange={(e) => setSymbol(e.target.value)}
                        options={SYMBOLS.map((s) => ({ value: s, label: s }))}
                    />
                    <Select
                        value={timeframe}
                        onChange={(e) => setTimeframe(e.target.value)}
                        options={TIMEFRAMES}
                    />
                    <button
                        onClick={() => refetch()}
                        className="p-2 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-800 transition-colors"
                        title="Refresh"
                    >
                        <RefreshCw className={`w-4 h-4 ${isFetching ? "animate-spin" : ""}`} />
                    </button>
                </div>
            }
        >
            {isLoading ? (
                <Spinner text={`Building report for ${symbol}...`} />
            ) : !report ? (
                <EmptyState title="No report available" description="Try refreshing or check your Zerodha connection." />
            ) : (
                <>
                    {/* Header stats */}
                    <Card>
                        <div className="flex items-start justify-between flex-wrap gap-4">
                            <div>
                                <p className="text-sm text-dark-500 uppercase tracking-wide">{symbol}</p>
                                <p className="text-5xl font-bold text-dark-50 font-mono mt-1">
                                    {spot?.ltp ?? "NA"}
                                </p>
                                {spot && (
                                    <p className={`text-lg font-mono mt-1 ${changePositive ? "text-green-400" : "text-red-400"}`}>
                                        {changePositive ? "+" : ""}{spot.change} ({spot.change_percent}%)
                                    </p>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                <Badge variant={report.session?.is_live ? "green" : "gray"}>
                                    {report.session?.session ?? "NA"}
                                </Badge>
                                {lastAnalysis && (
                                    <span className="text-xs text-dark-500">
                                        Last analysis: {lastAnalysis.minutes_ago}m ago · {lastAnalysis.signal}
                                        {lastAnalysis.confidence != null && ` (${lastAnalysis.confidence}%)`}
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Range bar — where LTP actually sits within today's
                            Low-High range, with a tick for Open. Reassembles
                            four separate numbers (LTP, Open, High, Low) into
                            one glanceable visual instead of four disconnected
                            stat boxes. Same pattern as the Dashboard's index
                            cards, kept consistent across the app. */}
                        <div className="mt-4 pt-4 border-t border-dark-800">
                            {spot?.low != null && spot?.high != null && spot.high > spot.low ? (
                                <>
                                    <div className="relative h-1.5 rounded-full bg-dark-800 mt-2 mb-3">
                                        {(() => {
                                            const low = parseFloat(spot.low);
                                            const high = parseFloat(spot.high);
                                            const open = parseFloat(spot.open);
                                            const ltp = parseFloat(spot.ltp);
                                            const pct = (v) =>
                                                Math.min(100, Math.max(0, ((v - low) / (high - low)) * 100));
                                            return (
                                                <>
                                                    <div
                                                        className="absolute top-1/2 -translate-y-1/2 w-px h-3 bg-dark-500"
                                                        style={{ left: `${pct(open)}%` }}
                                                        title={`Open ${spot.open}`}
                                                    />
                                                    <div
                                                        className={`absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full
                              border-2 border-dark-900 ${changePositive ? "bg-green-400" : "bg-red-400"}`}
                                                        style={{ left: `${pct(ltp)}%` }}
                                                        title={`LTP ${spot.ltp}`}
                                                    />
                                                </>
                                            );
                                        })()}
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <div>
                                            <span className="text-dark-500">Low </span>
                                            <span className="font-mono text-red-400 font-medium">{spot.low}</span>
                                        </div>
                                        <div className="text-xs text-dark-600">
                                            Open <span className="font-mono text-dark-400">{spot.open}</span>
                                        </div>
                                        <div>
                                            <span className="text-dark-500">High </span>
                                            <span className="font-mono text-green-400 font-medium">{spot.high}</span>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <p className="text-sm text-dark-600">Today's range unavailable.</p>
                            )}
                        </div>

                        {/* Reference — condensed to one muted line so it reads as
                            background context, not competing with today's data. */}
                        <p className="text-xs text-dark-600 mt-3">
                            Prev Close <span className="text-dark-400 font-mono">{spot?.close ?? "NA"}</span>
                            <span className="mx-2">·</span>
                            {report.range_label ? `${report.range_label} Range` : "Range"}{" "}
                            <span className="text-dark-400 font-mono">
                                {report.range_low && report.range_high
                                    ? `${report.range_low} – ${report.range_high}`
                                    : "NA"}
                            </span>
                        </p>
                    </Card>

                    {/* AI signal + suggested contract — right after the header,
                        so "should I do anything today" is answered before
                        scrolling into the technical detail below. */}
                    <AIAnalysisSection symbol={symbol} timeframe={timeframe} />

                    {/* Price chart */}
                    {report.price_history?.length > 0 && (
                        <Card title={`${symbol} — ${report.range_label || ""} Price Action`} subtitle="Close with EMA 20 / EMA 50 overlay">
                            <ResponsiveContainer width="100%" height={280}>
                                <LineChart data={report.price_history}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                    <XAxis dataKey="date" hide />
                                    <YAxis domain={["auto", "auto"]} tick={{ fill: "#64748b", fontSize: 11 }} />
                                    <Tooltip
                                        contentStyle={{
                                            background: "#1e293b",
                                            border: "1px solid #334155",
                                            borderRadius: "8px",
                                        }}
                                        labelStyle={{ color: "#94a3b8" }}
                                    />
                                    <Line type="monotone" dataKey="close" stroke="#3b82f6" dot={false} strokeWidth={2} name="Close" />
                                    <Line type="monotone" dataKey="ema_20" stroke="#f59e0b" dot={false} strokeWidth={1.5} strokeDasharray="4 4" name="EMA 20" />
                                    <Line type="monotone" dataKey="ema_50" stroke="#a78bfa" dot={false} strokeWidth={1.5} strokeDasharray="4 4" name="EMA 50" />
                                </LineChart>
                            </ResponsiveContainer>
                        </Card>
                    )}

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {/* Multi-timeframe trend */}
                        <Card title="Multi-Timeframe Trend">
                            <TrendRow label="5 Minute" data={report.multi_timeframe?.["5m"]} />
                            <TrendRow label="15 Minute" data={report.multi_timeframe?.["15m"]} />
                            <TrendRow label="30 Minute" data={report.multi_timeframe?.["30m"]} />
                        </Card>

                        {/* Support & Resistance */}
                        <Card title="Support & Resistance">
                            {sr ? (
                                <div className="space-y-3">
                                    <div>
                                        <p className="text-xs text-dark-500 mb-1">CPR</p>
                                        <div className="flex gap-4 text-sm font-mono">
                                            <span className="text-green-400">TC {sr.cpr?.tc ?? "NA"}</span>
                                            <span className="text-dark-300">PP {sr.cpr?.pp ?? "NA"}</span>
                                            <span className="text-red-400">BC {sr.cpr?.bc ?? "NA"}</span>
                                        </div>
                                    </div>
                                    <div>
                                        <p className="text-xs text-dark-500 mb-1">Pivot Points</p>
                                        <div className="grid grid-cols-3 gap-2 text-xs font-mono text-dark-300">
                                            <span className="text-red-400">R3 {sr.pivot?.r3 ?? "NA"}</span>
                                            <span className="text-red-400">R2 {sr.pivot?.r2 ?? "NA"}</span>
                                            <span className="text-red-400">R1 {sr.pivot?.r1 ?? "NA"}</span>
                                            <span className="text-green-400">S1 {sr.pivot?.s1 ?? "NA"}</span>
                                            <span className="text-green-400">S2 {sr.pivot?.s2 ?? "NA"}</span>
                                            <span className="text-green-400">S3 {sr.pivot?.s3 ?? "NA"}</span>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <p className="text-sm text-dark-600">No data available</p>
                            )}
                        </Card>
                    </div>

                    {/* ATM Options */}
                    <Card
                        title="ATM Option Analysis"
                        subtitle={options ? `Strike ${options.atm_strike} · Expiry ${options.expiry}` : undefined}
                    >
                        {options ? (
                            <>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <OptionSideCard label="Call (CE)" data={options.atm_call} accent="green" />
                                    <OptionSideCard label="Put (PE)" data={options.atm_put} accent="red" />
                                </div>
                                <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-dark-800">
                                    <StatBlock label="PCR (OI)" value={options.pcr_oi} />
                                    <StatBlock label="PCR (Volume)" value={options.pcr_volume} />
                                    <StatBlock label="Max Pain" value={options.max_pain} />
                                </div>
                            </>
                        ) : (
                            <p className="text-sm text-dark-600">
                                Option data unavailable — check NFO instrument data and Zerodha connection.
                            </p>
                        )}
                    </Card>
                </>
            )}
        </PageWrapper>
    );
}