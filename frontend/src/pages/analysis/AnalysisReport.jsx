import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { RefreshCw, TrendingUp, TrendingDown, Minus, AlertTriangle, Sparkles } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Badge, Select, Spinner, EmptyState, Button } from "../../components/common";
import { marketAPI } from "../../api/market";
import { analysisAPI } from "../../api/analysis";
import SignalCard from "./components/SignalCard";
import AIInsightsPanel from "./components/AIInsightsPanel";
import AIResponseView from "./components/AIResponseView";
import WorkspaceLearning, {
    MarketDriversPanel,
    DecisionEvidence,
    RecentAnalysis,
} from "./components/WorkspaceLearning";

const SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"];
const TIMEFRAMES = [
    { value: "5m", label: "5 Min" },
    { value: "15m", label: "15 Min" },
    { value: "30m", label: "30 Min" },
    { value: "1h", label: "1 Hour" },
];
const FORECAST_HORIZONS = [
    { value: "5", label: "5 Min" },
    { value: "15", label: "15 Min" },
    { value: "30", label: "30 Min" },
    { value: "60", label: "60 Min" },
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
    if (lower.includes("timed out") || lower.includes("timeout")) {
        return "The analysis took too long to return. Please retry; if this keeps happening, check the backend and Gemini provider status.";
    }
    if (lower.includes("network error") || lower.includes("could not reach athena")) {
        return "Athena's backend could not be reached. Check that the backend server is running, then retry.";
    }
    if (lower.includes("gemini_api_key is not configured")) {
        return "Gemini is selected, but GEMINI_API_KEY is not configured on the backend.";
    }
    if (lower.includes("anthropic_api_key not set")) {
        return "No Anthropic API key is configured on the backend. Add ANTHROPIC_API_KEY to your .env file and restart the server.";
    }
    if (lower.includes("groq_api_key not set")) {
        return "Groq is selected, but GROQ_API_KEY is not configured on the backend.";
    }
    if (lower.includes("rate limit") || lower.includes("429")) {
        return "The selected AI provider rate limit or quota was reached. Wait a moment or check its project quota.";
    }
    if (lower.includes("live data not available") || lower.includes("no candle data")) {
        return "No market data is available for this symbol yet, so no analysis could be run.";
    }
    return rawError;
}

function PromptPreviewPanel({ preview, loading, error }) {
    if (loading) {
        return (
            <div className="mt-4 rounded-lg border border-dark-700 bg-dark-900/50 p-4 text-sm text-dark-300">
                Building the prompt and collecting read-only market evidence… Gemini will not be
                called.
            </div>
        );
    }
    if (error) {
        return (
            <div className="mt-4 rounded-lg border border-red-500/40 bg-red-950/30 p-4 text-sm text-red-300">
                Could not build the preview: {error}
            </div>
        );
    }
    if (!preview) return null;

    const evidence = preview.rule_evidence || {};
    const parameters = preview.parameters || evidence.parameters || [];
    const parameterValue = (item) => {
        if (item.key === "oi_clamp") return `±${Number(item.value) * 100}%`;
        if (item.key === "profit_margin") return `${item.value}×`;
        if (item.key.startsWith("momentum_")) return `${item.value}×`;
        if (item.unit === "proposed points") return `${item.value} pts`;
        return `${item.value} ${item.unit}`;
    };
    const parameterStatus = (item) =>
        item.applied
            ? item.status === "active_display_scale"
                ? "Display scale"
                : "Active reference"
            : item.status === "inactive_data_unavailable"
              ? "Inactive · data unavailable"
              : "Inactive · not calibrated";

    return (
        <div className="mt-4 space-y-3 rounded-xl border border-dark-700 bg-dark-950/50 p-4">
            <div>
                <h4 className="text-sm font-semibold text-dark-100">
                    {preview.actual_request
                        ? `Exact prompts from the latest AI request · ${preview.provider_call_made ? "provider request attempted" : "provider not reached"}`
                        : "Prompt preview · no AI provider request made"}
                </h4>
                <p className="mt-1 text-xs text-dark-400">
                    {preview.symbol} · {preview.timeframe} candles ·{" "}
                    {preview.forecast_horizon_minutes} minute horizon · Provider: {preview.provider}{" "}
                    · Model: {preview.model} · Prompt: {preview.prompt_version || "default"}
                    {preview.generated_at
                        ? ` · Evidence assembled ${new Date(preview.generated_at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} IST`
                        : ""}
                </p>
                <p
                    className={`mt-2 text-xs ${preview.template_source === "database" ? "text-emerald-300" : "text-amber-300"}`}
                >
                    {preview.template_source === "database"
                        ? `Active database template: ${preview.template_name || "unnamed"}. Athena's current output and safety contract is appended at runtime.`
                        : "No active database template is configured for this analysis type. Athena is using its built-in versioned prompt and appending the current output and safety contract."}
                </p>
                {preview.market_context_error && (
                    <p className="mt-2 text-xs text-amber-300">
                        Market data note: {preview.market_context_error}
                    </p>
                )}
            </div>

            <div>
                <h5 className="mb-2 text-xs font-semibold uppercase tracking-wide text-dark-400">
                    All nine reference parameters
                </h5>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
                    {parameters.map((item) => (
                        <div
                            key={item.key}
                            className="rounded-lg border border-dark-700 bg-dark-900/60 p-3"
                        >
                            <div className="flex items-start justify-between gap-2">
                                <span className="text-xs text-dark-300">{item.label}</span>
                                <span
                                    className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] ${item.applied ? "bg-emerald-950/70 text-emerald-300" : "bg-amber-950/70 text-amber-300"}`}
                                >
                                    {parameterStatus(item)}
                                </span>
                            </div>
                            <p className="mt-2 font-mono text-sm font-semibold text-dark-100">
                                {parameterValue(item)}
                            </p>
                            {item.reason && (
                                <p className="mt-1 text-[11px] leading-4 text-dark-500">
                                    {item.reason}
                                </p>
                            )}
                        </div>
                    ))}
                </div>
                <p className="mt-2 text-[11px] text-dark-500">
                    Inactive bonuses are shown for transparency; Athena does not add them to a
                    score. The OI clamp is also inactive until comparable OI changes can be
                    verified.
                </p>
            </div>

            <details className="rounded-lg border border-dark-700 bg-dark-900/40 p-3">
                <summary className="cursor-pointer text-sm font-medium text-dark-200">
                    Evidence values, sources, and availability
                </summary>
                <pre className="mt-3 max-h-[360px] overflow-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-dark-300">
                    {JSON.stringify(evidence, null, 2)}
                </pre>
            </details>
            <details className="rounded-lg border border-dark-700 bg-dark-900/40 p-3">
                <summary className="cursor-pointer text-sm font-medium text-dark-200">
                    System prompt{" "}
                    {preview.actual_request ? "used for this attempt" : "for the next attempt"}
                </summary>
                <pre className="mt-3 max-h-[360px] overflow-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-dark-300">
                    {preview.system_prompt}
                </pre>
            </details>
            <details className="rounded-lg border border-dark-700 bg-dark-900/40 p-3">
                <summary className="cursor-pointer text-sm font-medium text-dark-200">
                    Market prompt and evidence{" "}
                    {preview.actual_request ? "used for this attempt" : "for the next attempt"}
                </summary>
                <pre className="mt-3 max-h-[480px] overflow-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-dark-300">
                    {preview.user_prompt}
                </pre>
            </details>
        </div>
    );
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
                <span className="text-xs text-dark-500">Not enough candle data</span>
            </div>
        );
    }
    const config = TREND_CONFIG[data.trend] || TREND_CONFIG.Neutral;
    const Icon = config.icon;
    const trendText =
        data.trend === "Bullish"
            ? "Above EMA 20"
            : data.trend === "Bearish"
              ? "Below EMA 20"
              : data.trend === "Neutral"
                ? "At EMA 20"
                : "Unavailable";
    return (
        <div className="flex items-center justify-between py-2 border-b border-dark-800 last:border-0">
            <span className="text-xs text-dark-300">{label}</span>
            <div className="flex items-center gap-2 shrink-0">
                <span
                    className="text-xs text-dark-400 font-mono"
                    title="RSI is a momentum measure, not a standalone entry signal."
                >
                    RSI 14 {data.rsi_14 ?? "—"}
                </span>
                <Badge variant={config.variant}>
                    <Icon className="w-3 h-3 inline mr-1" />
                    {trendText}
                </Badge>
            </div>
        </div>
    );
}

function OptionSideCard({ label, data, accent, compact = false }) {
    const isCall = label.toLowerCase().includes("call");
    if (compact && data) {
        return (
            <div
                className={`analysis-option-side rounded-lg border p-3 ${isCall ? "border-green-500/30" : "border-red-500/30"}`}
            >
                <p
                    className={`text-xs font-semibold ${isCall ? "text-green-400" : "text-red-400"}`}
                >
                    {label}
                </p>
                <p className="text-xl font-bold font-mono text-dark-50 mt-2">
                    ₹
                    {Number(data.ltp).toLocaleString("en-IN", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                    })}
                </p>
                <p className="text-[10px] text-dark-400">premium / unit</p>
                <dl className="mt-3 space-y-1 text-xs text-dark-300">
                    {[
                        ["IV", data.iv == null ? "—" : `${data.iv}%`],
                        ["Theta", data.theta],
                        ["Delta", data.delta],
                        ["Gamma", data.gamma],
                        ["OI", data.oi?.toLocaleString("en-IN")],
                    ].map(([name, value]) => (
                        <div key={name} className="flex flex-wrap justify-between gap-1">
                            <dt>{name}</dt>
                            <dd className="font-mono">{value ?? "—"}</dd>
                        </div>
                    ))}
                </dl>
            </div>
        );
    }
    if (!data) {
        return (
            <Card className={`analysis-option-side border-l-2 border-${accent}-500/40`}>
                <p className="text-xs text-dark-500">{label}</p>
                <p className="text-sm text-dark-500 mt-2">Quote unavailable</p>
            </Card>
        );
    }
    return (
        <Card className={`border-l-2 border-${accent}-500/40`}>
            <p className={`text-xs font-medium text-${accent}-400 uppercase tracking-wide`}>
                {label}
            </p>
            <p className="sr-only">
                {isCall
                    ? "Call · benefits from an upward move, all else equal"
                    : "Put · benefits from a downward move, all else equal"}
            </p>
            <p className="text-xl font-bold text-dark-50 font-mono mt-2">
                ₹{data.ltp}{" "}
                <span className="text-xs font-normal text-dark-400">premium / unit</span>
            </p>
            <div className="grid grid-cols-1 gap-2 mt-3 text-xs">
                <div title="Open interest: outstanding contracts, not buy or sell orders.">
                    <p className="text-dark-500">Open interest</p>
                    <p className="text-dark-300 font-mono">{data.oi?.toLocaleString()}</p>
                </div>
                <div title="Implied volatility: the volatility level reflected in the option price; it is not a direction forecast.">
                    <p className="text-dark-500">Implied volatility</p>
                    <p className="text-dark-300 font-mono">{data.iv}%</p>
                </div>
                <div title="Estimated premium sensitivity to a one-point move in the underlying. Delta is not a probability of profit.">
                    <p className="text-dark-500">Delta · price sensitivity</p>
                    <p className="text-dark-300 font-mono">{data.delta}</p>
                </div>
                <div title="Model-estimated daily time decay per option unit, assuming other inputs stay the same.">
                    <p className="text-dark-500">Theta · estimated daily decay</p>
                    <p className="text-dark-300 font-mono">{data.theta}</p>
                </div>
            </div>
        </Card>
    );
}

function AIAnalysisSection({
    symbol,
    timeframe,
    forecastHorizon,
    analysisMode,
    onMarketDrivers,
    onResultChange,
    actionTarget,
}) {
    const [paperEvaluate, setPaperEvaluate] = useState(true);
    const [aiResult, setAiResult] = useState(null);
    const [promptPreview, setPromptPreview] = useState(null);
    const [previewError, setPreviewError] = useState(null);
    const [previewOpen, setPreviewOpen] = useState(false);
    const sessionId = aiResult?.session_id;
    const { data: savedSession } = useQuery({
        queryKey: ["analysis-forecast-session", sessionId],
        queryFn: () => analysisAPI.getSession(sessionId),
        enabled: Boolean(sessionId) && !aiResult?.error,
        select: (res) => res.data.data,
        refetchInterval: (query) =>
            query.state.data?.forecast_outcome_status === "PENDING" ||
            ["OPEN", "WAITING_EXIT", "PARTIAL_EXIT"].includes(
                query.state.data?.paper_evaluation?.status
            )
                ? 30_000
                : false,
    });

    useEffect(() => {
        if (!savedSession) return;
        setAiResult((current) => {
            if (!current || current.session_id !== savedSession.id) return current;
            return {
                ...current,
                prompt_version: savedSession.prompt_version || current.prompt_version,
                paper_evaluation: savedSession.paper_evaluation,
                forecast_tracking: {
                    ...current.forecast_tracking,
                    status: savedSession.forecast_outcome_status,
                    horizon_minutes: savedSession.forecast_horizon_minutes,
                    target_time: savedSession.forecast_target_time,
                    anchor_price: savedSession.forecast_anchor_price,
                    actual_class: savedSession.forecast_actual_class || null,
                    outcome_price: savedSession.forecast_outcome_price,
                    resolved_at: savedSession.forecast_resolved_at,
                    brier_score: savedSession.forecast_brier_score,
                    method_version: savedSession.probability_method_version,
                },
                forecast_calibration:
                    savedSession.forecast_calibration ?? current.forecast_calibration,
                paper_trade_learning:
                    savedSession.paper_trade_learning ?? current.paper_trade_learning,
            };
        });
    }, [savedSession]);

    // Symbol/timeframe changed — the previous AI result no longer applies
    // to what's on screen, so clear it rather than showing a stale signal.
    useEffect(() => {
        setAiResult(null);
        setPromptPreview(null);
        setPreviewError(null);
        setPreviewOpen(false);
    }, [symbol, timeframe, forecastHorizon, analysisMode]);

    const { mutate: buildPreview, isPending: isPreviewPending } = useMutation({
        mutationFn: () =>
            analysisAPI.preview({
                symbol,
                timeframe,
                forecast_horizon_minutes: Number(forecastHorizon),
                analysis_mode: analysisMode,
                session_type: "MARKET_ANALYSIS",
                persist: false,
            }),
        onSuccess: (res) => {
            setPromptPreview(res.data.data);
            setPreviewError(null);
        },
        onError: (error) => {
            const message =
                error.response?.data?.errors?.detail ||
                error.response?.data?.message ||
                "Athena could not build the prompt preview.";
            setPreviewError(message);
            setPromptPreview(null);
        },
    });

    const { mutate: runAI, isPending } = useMutation({
        mutationFn: () =>
            analysisAPI.analyze({
                symbol,
                timeframe,
                forecast_horizon_minutes: Number(forecastHorizon),
                analysis_mode: analysisMode,
                session_type: "MARKET_ANALYSIS",
                persist: true,
                paper_evaluate: analysisMode === "LIVE" && paperEvaluate,
            }),
        onSuccess: (res) => {
            const data = res.data.data;
            setAiResult(data);
            if (data.user_prompt) {
                setPromptPreview({
                    ...data,
                    actual_request: true,
                    generated_at: data.rule_evidence?.as_of,
                });
            }
        },
        onError: (error) => {
            const responseMessage = error.response?.data?.message || error.response?.data?.detail;
            const message =
                error.code === "ECONNABORTED"
                    ? "The analysis request timed out before Athena returned a result."
                    : error.code === "ERR_NETWORK"
                      ? "Could not reach Athena's backend. Check that the backend server is running."
                      : responseMessage || "Athena could not complete the analysis request.";
            setAiResult({ error: message });
        },
    });

    const hasError = Boolean(aiResult?.error);

    useEffect(() => {
        onMarketDrivers?.(aiResult?.market_drivers || promptPreview?.market_drivers || null);
    }, [aiResult, promptPreview, onMarketDrivers]);

    useEffect(() => {
        onResultChange?.(aiResult?.error ? null : aiResult);
    }, [aiResult, onResultChange]);

    return (
        <>
            {actionTarget &&
                createPortal(
                    <Button
                        variant="primary"
                        size="md"
                        icon={Sparkles}
                        loading={isPending}
                        onClick={() => {
                            setAiResult(null);
                            runAI();
                        }}
                    >
                        {isPending
                            ? "Athena is analyzing…"
                            : analysisMode === "NEXT_SESSION"
                              ? "Create next-session outlook"
                              : aiResult
                                ? "Refresh analysis"
                                : "Run analysis"}
                    </Button>,
                    actionTarget
                )}
            <Card
                title="Athena analysis"
                subtitle={
                    analysisMode === "NEXT_SESSION"
                        ? `Next-session outlook · the historical ${forecastHorizon}-minute baseline starts at 09:15 IST`
                        : `Live-session assessment · the ${forecastHorizon}-minute probability is measured from matched historical outcomes`
                }
                actions={
                    <div className="flex flex-wrap items-center gap-2">
                        <Button
                            variant="secondary"
                            size="sm"
                            disabled={isPending}
                            loading={isPreviewPending}
                            onClick={() => {
                                if (promptPreview?.actual_request) {
                                    setPreviewOpen((open) => !open);
                                    return;
                                }
                                setPreviewOpen(true);
                                setPreviewError(null);
                                buildPreview();
                            }}
                        >
                            {promptPreview?.actual_request ? "View AI input" : "Preview AI input"}
                        </Button>
                    </div>
                }
            >
                {analysisMode === "LIVE" ? (
                    <div className="mb-4 rounded-lg border border-dark-700 bg-dark-900/40 p-3">
                        <label className="flex items-center gap-2 text-sm font-medium text-dark-200">
                            <input
                                type="checkbox"
                                checked={paperEvaluate}
                                disabled={isPending}
                                onChange={(event) => setPaperEvaluate(event.target.checked)}
                            />
                            Include a paper-trade simulation when eligible
                        </label>
                        <p className="ml-6 mt-1 text-xs leading-5 text-dark-400">
                            Paper only: one option lot is simulated for an eligible directional
                            signal, or one ATM CE+PE pair when the separate experimental volatility
                            gate passes. Entries and exits use verified quotes; this never places a
                            Zerodha order.
                        </p>
                    </div>
                ) : (
                    <p className="mb-4 text-xs text-amber-300">
                        Planning outlook only. No live entry, signal, or paper trade will be
                        created.
                    </p>
                )}
                {!aiResult ? (
                    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-dark-700 bg-dark-900/20 px-4 py-6 text-center">
                        <p className="text-dark-200 text-sm font-medium">Your analysis is ready</p>
                        <p className="mt-1 max-w-2xl text-xs leading-5 text-dark-400">
                            Check the market, candle interval, and forecast horizon above, then
                            select{" "}
                            <strong className="text-dark-200">
                                {analysisMode === "NEXT_SESSION"
                                    ? "Create next-session outlook"
                                    : "Run analysis"}
                            </strong>
                            . Athena explains its evidence and uncertainty; this does not place an
                            order.
                        </p>
                    </div>
                ) : hasError ? (
                    <div className="flex items-start gap-3 p-1">
                        <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                        <div>
                            <p className="text-sm font-medium text-red-400">Analysis failed</p>
                            <p className="text-sm text-dark-300 mt-1">
                                {friendlyErrorMessage(aiResult.error)}
                            </p>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <SignalCard result={aiResult} />
                        <DecisionEvidence result={aiResult} />
                        <AIInsightsPanel result={aiResult} />
                        <details>
                            <summary className="cursor-pointer text-sm text-dark-300">
                                Original AI prose · may differ from the validated fields above
                            </summary>
                            <AIResponseView response={aiResult.reasoning} />
                        </details>
                    </div>
                )}
                {previewOpen && (
                    <PromptPreviewPanel
                        preview={promptPreview}
                        loading={isPreviewPending}
                        error={previewError}
                    />
                )}
            </Card>
        </>
    );
}

export default function AnalysisReport() {
    const [symbol, setSymbol] = useState("NIFTY");
    const [timeframe, setTimeframe] = useState("5m");
    const [forecastHorizon, setForecastHorizon] = useState("15");
    const [analysisMode, setAnalysisMode] = useState("LIVE");
    const [marketDriversSnapshot, setMarketDriversSnapshot] = useState(null);
    const [latestAnalysis, setLatestAnalysis] = useState(null);
    const [actionTarget, setActionTarget] = useState(null);
    const [levelTab, setLevelTab] = useState("cpr");

    const {
        data: report,
        isLoading,
        isFetching,
        refetch,
    } = useQuery({
        queryKey: ["analysis-report", symbol],
        queryFn: () => marketAPI.getAnalysisReport(symbol),
        select: (res) => res.data.data,
    });

    const spot = report?.spot;
    const changePositive = spot && parseFloat(spot.change) >= 0;
    const sr = report?.support_resistance;
    const options = report?.options;
    const lastAnalysis = report?.last_analysis;
    const fiveMinuteTrend = report?.multi_timeframe?.["5m"]?.trend;
    const fifteenMinuteTrend = report?.multi_timeframe?.["15m"]?.trend;
    const shortTermAligned =
        ["Bullish", "Bearish"].includes(fiveMinuteTrend) && fiveMinuteTrend === fifteenMinuteTrend;

    return (
        <PageWrapper
            className="analysis-workspace"
            headerClassName="analysis-workspace-header card"
            headerContent={
                <section aria-label="Market and analysis setup">
                    <Card className="px-3 py-2">
                        <div className="grid grid-cols-1 items-end gap-2 sm:grid-cols-2 xl:grid-cols-4">
                            <Select
                                label="Market"
                                value={symbol}
                                onChange={(e) => setSymbol(e.target.value)}
                                options={SYMBOLS.map((s) => ({ value: s, label: s }))}
                            />
                            <Select
                                label="Candle interval"
                                value={timeframe}
                                onChange={(e) => setTimeframe(e.target.value)}
                                options={TIMEFRAMES}
                            />
                            <Select
                                label="Forecast horizon"
                                value={forecastHorizon}
                                onChange={(e) => setForecastHorizon(e.target.value)}
                                options={FORECAST_HORIZONS}
                            />
                            <Select
                                label="Analysis mode"
                                value={analysisMode}
                                onChange={(e) => setAnalysisMode(e.target.value)}
                                options={[
                                    { value: "LIVE", label: "Live session" },
                                    { value: "NEXT_SESSION", label: "Next session outlook" },
                                ]}
                            />
                        </div>
                        {analysisMode === "NEXT_SESSION" && (
                            <p className="mt-2 rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-1.5 text-xs text-amber-200">
                                Planning only: next-session outlook from the 09:15 IST open. It
                                cannot create a signal or paper trade.
                            </p>
                        )}
                    </Card>
                </section>
            }
            title="AI Analysis"
            subtitle="Choose a market and forecast horizon, review the verified data, then ask Athena for a conditional analysis."
            actions={
                <div className="flex flex-wrap items-center justify-end gap-3">
                    <a href="/analysis/history" className="btn-secondary">
                        Analysis history
                    </a>
                    <button
                        onClick={() => refetch()}
                        aria-label={
                            isFetching ? "Refreshing market snapshot" : "Refresh market snapshot"
                        }
                        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-dark-300 hover:text-dark-100 hover:bg-dark-800 transition-colors"
                        title="Refresh market snapshot"
                    >
                        <RefreshCw className={`w-4 h-4 ${isFetching ? "animate-spin" : ""}`} />
                        <span>{isFetching ? "Refreshing…" : "Refresh data"}</span>
                    </button>
                    <div ref={setActionTarget} />
                </div>
            }
        >
            {isLoading ? (
                <Spinner text={`Building report for ${symbol}...`} />
            ) : !report ? (
                <EmptyState
                    title="No report available"
                    description="Try refreshing or check your Zerodha connection."
                />
            ) : (
                <>
                    <section className="analysis-context-grid" aria-label="Market context">
                        {/* Header stats */}
                        <Card className="h-full">
                            <div className="flex items-start justify-between flex-wrap gap-2">
                                <div>
                                    <p className="text-xs text-dark-500 uppercase tracking-wide">
                                        {symbol}
                                    </p>
                                    <p className="text-3xl sm:text-4xl font-bold text-dark-50 font-mono leading-tight">
                                        {spot?.ltp ?? "NA"}
                                    </p>
                                    {spot && (
                                        <p
                                            className={`text-sm font-mono ${changePositive ? "text-green-400" : "text-red-400"}`}
                                        >
                                            {changePositive ? "+" : ""}
                                            {spot.change} ({spot.change_percent}%)
                                        </p>
                                    )}
                                </div>
                                <div className="flex items-center gap-2">
                                    <Badge variant={report.session?.is_live ? "green" : "gray"}>
                                        {report.session?.session ?? "NA"}
                                    </Badge>
                                    {lastAnalysis && (
                                        <span className="text-xs text-dark-500">
                                            Last analysis: {lastAnalysis.minutes_ago}m ago ·{" "}
                                            {lastAnalysis.signal}
                                            {lastAnalysis.confidence != null &&
                                                ` (${lastAnalysis.confidence}%)`}
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
                            <div className="mt-2 pt-2 border-t border-dark-800">
                                {spot?.low != null && spot?.high != null && spot.high > spot.low ? (
                                    <>
                                        <div className="relative h-1.5 rounded-full bg-dark-800 mt-1 mb-2">
                                            {(() => {
                                                const low = parseFloat(spot.low);
                                                const high = parseFloat(spot.high);
                                                const open = parseFloat(spot.open);
                                                const ltp = parseFloat(spot.ltp);
                                                const pct = (v) =>
                                                    Math.min(
                                                        100,
                                                        Math.max(
                                                            0,
                                                            ((v - low) / (high - low)) * 100
                                                        )
                                                    );
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
                                        <div className="flex items-center justify-between text-xs">
                                            <div>
                                                <span className="text-dark-500">Low </span>
                                                <span className="font-mono text-red-400 font-medium">
                                                    {spot.low}
                                                </span>
                                            </div>
                                            <div className="text-xs text-dark-600">
                                                Open{" "}
                                                <span className="font-mono text-dark-400">
                                                    {spot.open}
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-dark-500">High </span>
                                                <span className="font-mono text-green-400 font-medium">
                                                    {spot.high}
                                                </span>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <p className="text-sm text-dark-600">
                                        Today&apos;s range unavailable.
                                    </p>
                                )}
                            </div>

                            {/* Prior close is the only daily reference retained in this
                            intraday-focused workspace. */}
                            <p className="text-xs text-dark-600 mt-1">
                                Prev Close{" "}
                                <span className="text-dark-400 font-mono">
                                    {spot?.close ?? "NA"}
                                </span>
                            </p>
                        </Card>
                        {/* Multi-timeframe trend */}
                        <Card
                            title="Intraday trend check"
                            subtitle="Price compared with EMA 20 · RSI shows momentum."
                        >
                            <details
                                className={`mb-2 text-xs leading-5 ${shortTermAligned ? "text-green-400" : "text-yellow-400"}`}
                            >
                                <summary className="cursor-pointer">EMA alignment context</summary>
                                {shortTermAligned
                                    ? `Technical context: 5m and 15m are aligned ${fiveMinuteTrend.toLowerCase()} vs EMA 20. Check Athena’s separate option idea below; this alignment alone is not a trade signal.`
                                    : "Technical context: 5m and 15m readings conflict or are unavailable. Athena’s separate option idea below considers the full evidence; wait for price confirmation."}
                            </details>
                            <TrendRow
                                label="5 min · near-term"
                                data={report.multi_timeframe?.["5m"]}
                            />
                            <TrendRow
                                label="15 min · confirmation"
                                data={report.multi_timeframe?.["15m"]}
                            />
                            <TrendRow
                                label="30 min · broader context"
                                data={report.multi_timeframe?.["30m"]}
                            />
                        </Card>

                        {/* Support & Resistance */}
                        <Card
                            title="Intraday levels to watch"
                            subtitle="15-minute CPR and pivots · reference levels."
                        >
                            {sr ? (
                                <div className="space-y-3">
                                    <div
                                        className="flex gap-2"
                                        role="tablist"
                                        aria-label="Intraday level views"
                                    >
                                        {[
                                            ["cpr", "CPR"],
                                            ["pivot", "Pivot levels"],
                                            ["key", "Key levels"],
                                        ].map(([value, label]) => (
                                            <button
                                                key={value}
                                                id={`levels-tab-${value}`}
                                                type="button"
                                                role="tab"
                                                aria-selected={levelTab === value}
                                                aria-controls="levels-panel"
                                                onClick={() => setLevelTab(value)}
                                                className={
                                                    levelTab === value
                                                        ? "btn-primary btn-sm"
                                                        : "btn-secondary btn-sm"
                                                }
                                            >
                                                {label}
                                            </button>
                                        ))}
                                    </div>
                                    <div
                                        id="levels-panel"
                                        role="tabpanel"
                                        aria-labelledby={`levels-tab-${levelTab}`}
                                    >
                                        {levelTab === "cpr" && (
                                            <div className="rounded-lg border border-dark-700 bg-dark-900/30 p-3">
                                                <p className="text-xs text-dark-300">
                                                    Central Pivot Range (CPR)
                                                </p>
                                                <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                                                    <span className="text-dark-400">
                                                        Top (TC)
                                                        <br />
                                                        <strong className="font-mono text-green-400">
                                                            {sr.cpr?.tc ?? "—"}
                                                        </strong>
                                                    </span>
                                                    <span className="text-dark-400">
                                                        Pivot (PP)
                                                        <br />
                                                        <strong className="font-mono text-dark-200">
                                                            {sr.cpr?.pp ?? "—"}
                                                        </strong>
                                                    </span>
                                                    <span className="text-dark-400">
                                                        Bottom (BC)
                                                        <br />
                                                        <strong className="font-mono text-red-400">
                                                            {sr.cpr?.bc ?? "—"}
                                                        </strong>
                                                    </span>
                                                </div>
                                            </div>
                                        )}
                                        {levelTab === "pivot" && (
                                            <div className="rounded-lg border border-dark-700 bg-dark-900/30 p-3">
                                                <p className="text-xs text-dark-300">
                                                    Pivot levels
                                                </p>
                                                <div className="mt-2 grid grid-cols-3 gap-y-2 text-xs font-mono">
                                                    <span className="text-red-400">
                                                        R3 · {sr.pivot?.r3 ?? "—"}
                                                    </span>
                                                    <span className="text-red-400">
                                                        R2 · {sr.pivot?.r2 ?? "—"}
                                                    </span>
                                                    <span className="text-red-400">
                                                        R1 · {sr.pivot?.r1 ?? "—"}
                                                    </span>
                                                    <span className="text-green-400">
                                                        S1 · {sr.pivot?.s1 ?? "—"}
                                                    </span>
                                                    <span className="text-green-400">
                                                        S2 · {sr.pivot?.s2 ?? "—"}
                                                    </span>
                                                    <span className="text-green-400">
                                                        S3 · {sr.pivot?.s3 ?? "—"}
                                                    </span>
                                                </div>
                                            </div>
                                        )}
                                        {levelTab === "key" && (
                                            <div className="grid grid-cols-2 gap-3 text-xs">
                                                <StatBlock label="Session low" value={spot?.low} />
                                                <StatBlock
                                                    label="Session high"
                                                    value={spot?.high}
                                                />
                                                <StatBlock
                                                    label="Session open"
                                                    value={spot?.open}
                                                />
                                                <StatBlock
                                                    label="Previous close"
                                                    value={spot?.close}
                                                />
                                            </div>
                                        )}
                                    </div>
                                    <p className="sr-only">
                                        Watch how price behaves near these levels; a level alone
                                        does not confirm a trade.
                                    </p>
                                </div>
                            ) : (
                                <p className="text-sm text-dark-600">No data available</p>
                            )}
                        </Card>
                    </section>
                    <section
                        className="analysis-overview-grid"
                        aria-label="Market drivers, learning and options"
                    >
                        <MarketDriversPanel snapshot={marketDriversSnapshot} compact />
                        <WorkspaceLearning
                            key={`${symbol}-${forecastHorizon}`}
                            symbol={symbol}
                            horizon={forecastHorizon}
                            refreshKey={latestAnalysis?.session_id}
                            compact
                        />
                        {/* ATM Options */}
                        <Card
                            className="analysis-option-snapshot h-full min-w-0"
                            title="ATM option snapshot"
                            subtitle={
                                options
                                    ? `ATM ${options.atm_strike} · Expiry ${options.expiry}`
                                    : "Call and put prices at the strike nearest to the index price."
                            }
                        >
                            <details
                                className="mb-3 rounded-lg border border-primary-500/30 bg-primary-500/5 p-3"
                                open={Boolean(latestAnalysis)}
                            >
                                <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wide text-primary-300">
                                    Athena’s option idea
                                </summary>
                                {analysisMode === "NEXT_SESSION" ? (
                                    <p className="mt-1 text-sm text-dark-300">
                                        Next-session planning does not recommend a current CE or PE
                                        contract.
                                    </p>
                                ) : !latestAnalysis ? (
                                    <p className="mt-1 text-sm text-dark-300">
                                        Run a live analysis above to see whether Athena identifies a
                                        CE or PE candidate. The quotes below are market references
                                        only.
                                    </p>
                                ) : latestAnalysis.volatility_setup?.eligible ? (
                                    <>
                                        <p className="mt-1 text-base font-semibold text-amber-200">
                                            Experimental BOTH setup · paper testing only
                                        </p>
                                        <p className="mt-1 text-xs leading-5 text-dark-300">
                                            The deterministic volatility gate passed for a long ATM
                                            straddle. This is separate from Athena’s directional AI
                                            signal and is not available for live execution.
                                        </p>
                                        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                                            {latestAnalysis.volatility_setup.legs.map((leg) => (
                                                <div
                                                    key={leg.option_type}
                                                    className="rounded-lg border border-dark-700 bg-dark-900/40 p-3 text-xs"
                                                >
                                                    <p className="font-semibold text-dark-100">
                                                        Buy {leg.option_type} · {leg.trading_symbol}
                                                    </p>
                                                    <p className="mt-1 text-dark-300">
                                                        ATM {leg.strike} · Expiry {leg.expiry} · LTP
                                                        ₹{leg.entry_premium} · ask ₹
                                                        {leg.estimated_buy_price}
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                        <p className="mt-2 text-xs leading-5 text-dark-300">
                                            Expected{" "}
                                            {latestAnalysis.volatility_setup.horizon_minutes}-minute
                                            1σ move:{" "}
                                            {latestAnalysis.volatility_setup.expected_move_points}{" "}
                                            pts · combined ask debit: ₹
                                            {
                                                latestAnalysis.volatility_setup
                                                    .combined_premium_per_unit
                                            }
                                            /unit · gate hurdle:{" "}
                                            {latestAnalysis.volatility_setup.required_move_points}{" "}
                                            pts · one-lot premium-only loss estimate ₹
                                            {Number(
                                                latestAnalysis.volatility_setup
                                                    .maximum_loss_per_lot_before_taxes
                                            ).toLocaleString("en-IN")}{" "}
                                            before fees/taxes.
                                        </p>
                                        <p className="mt-1 text-[11px] leading-4 text-amber-200">
                                            {latestAnalysis.volatility_setup.method_note} Event
                                            calendar:{" "}
                                            {latestAnalysis.volatility_setup
                                                .event_calendar_status || "unknown"}
                                            .
                                        </p>
                                        {latestAnalysis.paper_evaluation?.strategy ===
                                            "LONG_STRADDLE" && (
                                            <p className="mt-2 text-xs text-dark-200">
                                                Paper simulation:{" "}
                                                {latestAnalysis.paper_evaluation.status} ·{" "}
                                                {latestAnalysis.paper_evaluation.reason}{" "}
                                                {latestAnalysis.paper_evaluation.net_pnl != null &&
                                                    `· combined net P&L ₹${latestAnalysis.paper_evaluation.net_pnl}`}
                                            </p>
                                        )}
                                        {latestAnalysis.paper_evaluation?.status === "SKIPPED" && (
                                            <p className="mt-2 text-xs text-amber-200">
                                                Paper simulation skipped:{" "}
                                                {latestAnalysis.paper_evaluation.reason}
                                            </p>
                                        )}
                                    </>
                                ) : latestAnalysis.signal === "BUY" ||
                                  latestAnalysis.signal === "SELL" ? (
                                    latestAnalysis.suggested_contract ? (
                                        (() => {
                                            const idea = latestAnalysis.suggested_contract;
                                            const oneLotCost =
                                                Number(idea.entry_premium) * Number(idea.lot_size);
                                            return (
                                                <>
                                                    <p className="mt-1 text-base font-semibold text-dark-100">
                                                        {latestAnalysis.signal === "BUY"
                                                            ? "Bullish candidate"
                                                            : "Bearish candidate"}{" "}
                                                        · Buy {idea.option_type} ·{" "}
                                                        {idea.trading_symbol}
                                                    </p>
                                                    <p className="mt-1 text-xs leading-5 text-dark-300">
                                                        {idea.moneyness ||
                                                            latestAnalysis.option_moneyness ||
                                                            "ATM"}{" "}
                                                        {idea.option_type} · Strike {idea.strike} ·
                                                        Expiry {idea.expiry} · Premium at analysis ₹
                                                        {idea.entry_premium}
                                                    </p>
                                                    {Number.isFinite(oneLotCost) && (
                                                        <p className="mt-1 text-xs text-dark-300">
                                                            Approx. one-lot premium ₹
                                                            {oneLotCost.toLocaleString("en-IN", {
                                                                maximumFractionDigits: 2,
                                                            })}{" "}
                                                            before fees; this is the buyer’s maximum
                                                            loss estimate.
                                                        </p>
                                                    )}
                                                    {latestAnalysis.option_selection_reason && (
                                                        <p className="mt-1 text-xs text-dark-400">
                                                            Why this strike type:{" "}
                                                            {latestAnalysis.option_selection_reason}
                                                        </p>
                                                    )}
                                                    {latestAnalysis.volatility_setup?.reasons
                                                        ?.length > 0 && (
                                                        <p className="mt-1 text-xs text-dark-500">
                                                            Experimental BOTH gate not eligible:{" "}
                                                            {latestAnalysis.volatility_setup.reasons
                                                                .slice(0, 2)
                                                                .join(" ")}
                                                        </p>
                                                    )}
                                                    <p className="mt-2 text-[11px] leading-4 text-amber-200">
                                                        Conditional analysis, not an order. Recheck
                                                        the live option price before deciding. A
                                                        paper result or AI confidence does not
                                                        guarantee profit.
                                                    </p>
                                                </>
                                            );
                                        })()
                                    ) : (
                                        <p className="mt-1 text-sm text-amber-200">
                                            Athena has a directional view but could not verify a
                                            listed option contract, so there is no CE/PE idea to
                                            review.
                                        </p>
                                    )
                                ) : (
                                    <>
                                        <p className="mt-1 text-sm font-semibold text-dark-100">
                                            No Trade · no CE or PE recommended
                                        </p>
                                        {latestAnalysis.no_trade_reason && (
                                            <p className="mt-1 text-xs text-dark-300">
                                                {latestAnalysis.no_trade_reason}
                                            </p>
                                        )}
                                        {latestAnalysis.volatility_setup?.reasons?.length > 0 && (
                                            <p className="mt-2 text-xs text-dark-400">
                                                Experimental BOTH gate: not eligible —{" "}
                                                {latestAnalysis.volatility_setup.reasons
                                                    .slice(0, 2)
                                                    .join(" ")}
                                            </p>
                                        )}
                                    </>
                                )}
                            </details>
                            {options ? (
                                <>
                                    <div className="grid grid-cols-2 gap-2">
                                        <OptionSideCard
                                            label="Call (CE)"
                                            data={options.atm_call}
                                            accent="green"
                                            compact
                                        />
                                        <OptionSideCard
                                            label="Put (PE)"
                                            data={options.atm_put}
                                            accent="red"
                                            compact
                                        />
                                    </div>
                                    <details className="mt-2">
                                        <summary className="cursor-pointer text-[10px] text-dark-400">
                                            Market ratios and quote notes
                                        </summary>
                                        <p className="mt-2 text-[10px] leading-4 text-dark-400">
                                            Quotes are references; Greeks are estimates, not odds of
                                            profit.
                                        </p>
                                        <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-dark-800">
                                            <StatBlock
                                                label="Put/Call ratio · open interest"
                                                value={options.pcr_oi}
                                            />
                                            <StatBlock
                                                label="Put/Call ratio · volume"
                                                value={options.pcr_volume}
                                            />
                                            <StatBlock
                                                label="Max pain · OI estimate, not target"
                                                value={options.max_pain}
                                            />
                                        </div>
                                    </details>
                                </>
                            ) : (
                                <p className="text-sm text-dark-600">
                                    Option data unavailable — check NFO instrument data and Zerodha
                                    connection.
                                </p>
                            )}
                        </Card>
                    </section>
                    <RecentAnalysis refreshKey={latestAnalysis?.session_id} />
                    <AIAnalysisSection
                        key={`${symbol}-${timeframe}-${forecastHorizon}-${analysisMode}`}
                        symbol={symbol}
                        timeframe={timeframe}
                        forecastHorizon={forecastHorizon}
                        analysisMode={analysisMode}
                        onMarketDrivers={setMarketDriversSnapshot}
                        onResultChange={setLatestAnalysis}
                        actionTarget={actionTarget}
                    />
                </>
            )}
        </PageWrapper>
    );
}
