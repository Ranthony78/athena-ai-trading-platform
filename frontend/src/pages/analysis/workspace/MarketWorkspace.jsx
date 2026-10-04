import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, Play, RefreshCw } from "lucide-react";
import { PageWrapper } from "../../../components/layout";
import { Button, Card, EmptyState, Select, Spinner } from "../../../components/common";
import { analysisAPI } from "../../../api/analysis";
import { marketAPI } from "../../../api/market";
import {
    ExpectationCard,
    FilterEngineCard,
    GapAnalysisCard,
    LevelsCard,
    CoreCalculationsCard,
    OiProfileCard,
    OptionSnapshotCard,
    OptionsSetupCard,
    OutlookCard,
    PriceStrip,
    ProfitProbabilityCard,
    TimeBlocksCard,
    TrendCheck,
    VerdictPanel,
} from "./WorkspaceCards";

const TIMEFRAMES = [
    { value: "5m", label: "5 Min" },
    { value: "15m", label: "15 Min" },
    { value: "30m", label: "30 Min" },
];
const HORIZONS = [
    { value: "15", label: "15 Min" },
    { value: "30", label: "30 Min" },
    { value: "60", label: "60 Min" },
];
const MODES = [
    { value: "LIVE", label: "Live session" },
    { value: "NEXT_SESSION", label: "Next session outlook" },
];

function errorText(error) {
    const data = error?.response?.data;
    return (
        data?.errors?.detail ||
        data?.message ||
        data?.detail ||
        "The analysis could not be completed. Check the backend and the AI connection, then retry."
    );
}

// One scrolling market workspace. The market is a prop, so NIFTY and
// BANKNIFTY share this page and differ only in the symbol.
export default function MarketWorkspace({ symbol, title }) {
    const [timeframe, setTimeframe] = useState("15m");
    const [horizon, setHorizon] = useState("15");
    const [mode, setMode] = useState("LIVE");

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

    const engine = useQuery({
        queryKey: ["options-engine", symbol, horizon, mode],
        queryFn: () => marketAPI.getOptionsEngine(symbol, { horizon, mode }),
        select: (res) => res.data.data,
        retry: false,
        staleTime: 60000,
    });
    const engineReason = engine.error?.response?.data?.message;

    const analysis = useMutation({
        mutationFn: () =>
            analysisAPI.analyze({
                symbol,
                timeframe,
                forecast_horizon_minutes: Number(horizon),
                analysis_mode: mode,
                session_type: "MARKET_ANALYSIS",
                persist: true,
                paper_evaluate: false,
            }),
    });

    const result = analysis.data?.data?.data;
    const resultError = analysis.isError ? errorText(analysis.error) : result?.error || null;
    const closed = report && !report.session?.is_live;

    return (
        <PageWrapper
            title={title}
            subtitle="Probability-based research on verified market data. Educational only, not trading advice."
            actions={
                <div className="flex flex-wrap items-center justify-end gap-3">
                    <Link to="/analysis" className="btn-ghost">
                        All markets
                    </Link>
                    <Link to="/analysis/detailed" className="btn-secondary">
                        Detailed report
                    </Link>
                    <button
                        type="button"
                        onClick={() => refetch()}
                        className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-dark-300 transition-colors hover:bg-dark-800 hover:text-dark-100"
                    >
                        <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
                        {isFetching ? "Refreshing…" : "Refresh data"}
                    </button>
                    <Button
                        icon={Play}
                        loading={analysis.isPending}
                        onClick={() => analysis.mutate()}
                    >
                        Run Analysis
                    </Button>
                </div>
            }
            headerContent={
                <Card className="mt-3 px-3 py-2">
                    <div className="grid grid-cols-1 items-end gap-2 sm:grid-cols-3">
                        <Select
                            label="Candle interval"
                            value={timeframe}
                            onChange={(e) => setTimeframe(e.target.value)}
                            options={TIMEFRAMES}
                        />
                        <Select
                            label="Forecast horizon"
                            value={horizon}
                            onChange={(e) => setHorizon(e.target.value)}
                            options={HORIZONS}
                        />
                        <Select
                            label="Analysis mode"
                            value={mode}
                            onChange={(e) => setMode(e.target.value)}
                            options={MODES}
                        />
                    </div>
                </Card>
            }
        >
            {closed && (
                <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-sm text-amber-200">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>
                        The market is {String(report.session?.session || "closed").toLowerCase()}.
                        Figures below are from the last completed session and may be stale.
                    </span>
                </div>
            )}

            {isLoading ? (
                <Spinner text={`Building the ${symbol} workspace…`} />
            ) : !report ? (
                <EmptyState
                    title="No data available"
                    description="Refresh, or check your Zerodha connection."
                />
            ) : (
                <>
                    <PriceStrip symbol={symbol} report={report} />
                    <VerdictPanel
                        result={result}
                        error={resultError}
                        running={analysis.isPending}
                        mode={mode}
                    />
                    <div className="grid gap-6 xl:grid-cols-2">
                        <TrendCheck report={report} />
                        <LevelsCard report={report} />
                        <GapAnalysisCard report={report} />
                        <OutlookCard result={result && !resultError ? result : null} />
                        <ExpectationCard
                            result={result && !resultError ? result : null}
                            spot={report.spot}
                        />
                        <OptionSnapshotCard report={report} />
                    </div>
                    <TimeBlocksCard report={report} />
                    <CoreCalculationsCard report={report} />
                    <FilterEngineCard
                        engine={engine.data}
                        loading={engine.isLoading}
                        reason={engineReason}
                    />
                    <ProfitProbabilityCard
                        horizon={horizon}
                        probability={engine.data?.profit_probability}
                        loading={engine.isLoading}
                        reason={engineReason}
                    />
                    <div className="grid gap-6 xl:grid-cols-2">
                        <OptionsSetupCard report={report} />
                        <OiProfileCard report={report} />
                    </div>
                </>
            )}
        </PageWrapper>
    );
}
