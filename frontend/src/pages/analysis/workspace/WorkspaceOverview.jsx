import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight, FileText } from "lucide-react";
import { PageWrapper } from "../../../components/layout";
import { Badge, Card, Spinner } from "../../../components/common";
import { marketAPI } from "../../../api/market";
import { isNumber, num, percent, signed, toNumber } from "./format";

const MARKETS = [
    { symbol: "NIFTY", label: "Nifty 50", to: "/analysis/nifty" },
    { symbol: "BANKNIFTY", label: "Bank Nifty", to: "/analysis/banknifty" },
];

// Nearest pivot or CPR level below and above the current price.
export function nearestLevels(report) {
    const price = toNumber(report?.spot?.ltp);
    const sr = report?.support_resistance;
    if (price === null || !sr) return { support: null, resistance: null };
    const levels = [...Object.values(sr.pivot || {}), ...Object.values(sr.cpr || {})]
        .map(toNumber)
        .filter((value) => value !== null && value > 0);
    const below = levels.filter((value) => value < price);
    const above = levels.filter((value) => value > price);
    return {
        support: below.length ? Math.max(...below) : null,
        resistance: above.length ? Math.min(...above) : null,
    };
}

function Fact({ label, value, tone }) {
    const color = tone === "up" ? "text-green-400" : tone === "down" ? "text-red-400" : "";
    return (
        <div className="rounded-lg bg-dark-800/60 p-3">
            <p className="text-[11px] uppercase tracking-wide text-dark-500">{label}</p>
            <p className={`mt-1 text-sm font-semibold font-mono text-dark-100 ${color}`}>{value}</p>
        </div>
    );
}

function lastReadText(lastAnalysis) {
    if (!lastAnalysis) return "No analysis run yet";
    const bias =
        lastAnalysis.signal === "BUY"
            ? "Bullish"
            : lastAnalysis.signal === "SELL"
              ? "Bearish"
              : "No clear edge";
    const confidence = lastAnalysis.confidence != null ? ` · ${lastAnalysis.confidence}%` : "";
    return `${bias}${confidence} · ${lastAnalysis.minutes_ago}m ago`;
}

function MarketCard({ market }) {
    const {
        data: report,
        isLoading,
        isError,
    } = useQuery({
        queryKey: ["analysis-report", market.symbol],
        queryFn: () => marketAPI.getAnalysisReport(market.symbol),
        select: (res) => res.data.data,
    });

    const change = toNumber(report?.spot?.change);
    const tone = change === null ? undefined : change >= 0 ? "up" : "down";
    const levels = nearestLevels(report);
    const vix = report?.key_metrics?.vix;
    const lastAnalysis = report?.last_analysis;
    const lastVariant =
        lastAnalysis?.signal === "BUY" ? "green" : lastAnalysis?.signal === "SELL" ? "red" : "gray";

    return (
        <Card
            title={market.label}
            actions={
                <Badge variant={report?.session?.is_live ? "green" : "gray"}>
                    {report?.session?.session ?? "NA"}
                </Badge>
            }
        >
            {isLoading ? (
                <Spinner text={`Loading ${market.label}…`} />
            ) : isError || !report ? (
                <p className="text-sm text-dark-500">
                    Unavailable: the market data could not be loaded. Check the backend and your
                    Zerodha connection.
                </p>
            ) : (
                <>
                    <p className="font-mono text-3xl font-bold text-dark-50">
                        {num(report.spot?.ltp)}
                    </p>
                    <p
                        className={`font-mono text-sm ${tone === "up" ? "text-green-400" : tone === "down" ? "text-red-400" : "text-dark-400"}`}
                    >
                        {change === null
                            ? "NA"
                            : `${signed(report.spot?.change)} (${percent(report.spot?.change_percent)})`}
                    </p>
                    <div className="mt-4 grid grid-cols-3 gap-2">
                        <Fact
                            label="India VIX"
                            value={
                                vix
                                    ? `${num(vix.ltp)}${isNumber(vix.change_pct) ? ` (${percent(vix.change_pct, 1)})` : ""}`
                                    : "NA"
                            }
                        />
                        <Fact label="Support" value={num(levels.support, 1)} />
                        <Fact label="Resistance" value={num(levels.resistance, 1)} />
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-dark-300">
                        <span>Last read:</span>
                        <Badge variant={lastAnalysis ? lastVariant : "gray"}>
                            {lastReadText(lastAnalysis)}
                        </Badge>
                    </div>
                </>
            )}
            <Link to={market.to} className="btn-primary mt-4 w-full">
                Open {market.label} workspace
                <ArrowRight className="h-4 w-4" />
            </Link>
        </Card>
    );
}

// The starting page for the AI Workspace: one card per market, each leading
// to its own full workspace.
export default function WorkspaceOverview() {
    const { data: closed } = useQuery({
        queryKey: ["analysis-overview-session"],
        queryFn: () => marketAPI.getSession(),
        select: (res) => res.data.data,
        refetchInterval: 60000,
    });
    const marketClosed = closed && closed.is_live === false;

    return (
        <PageWrapper
            title="Athena AI Workspace"
            subtitle="Pick a market. Each workspace explains what the verified data says, where it is unsure, and never places an order."
            actions={
                <Link to="/analysis/detailed" className="btn-secondary">
                    <FileText className="h-4 w-4" />
                    Detailed report
                </Link>
            }
        >
            {marketClosed && (
                <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-sm text-amber-200">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>
                        The market is {String(closed.session || "closed").toLowerCase()}. Figures
                        are from the last completed session and may be stale.
                    </span>
                </div>
            )}
            <div className="grid gap-6 lg:grid-cols-2">
                {MARKETS.map((market) => (
                    <MarketCard key={market.symbol} market={market} />
                ))}
            </div>
            <p className="text-xs text-dark-500">
                Probability-based research for education. It is not trading advice.
            </p>
        </PageWrapper>
    );
}
