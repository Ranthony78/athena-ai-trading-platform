import { useEffect, useRef, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
    Activity,
    ArrowDownRight,
    ArrowRight,
    ArrowUpRight,
    Clock3,
    Radio,
    ShieldAlert,
    ShieldCheck,
} from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Select, Spinner } from "../../components/common";
import CandleChart from "../../components/charts/CandleChart";
import AISignalCard from "./components/AISignalCard";
import PortfolioCard from "./components/PortfolioCard";
import DashboardMarketPanels from "./components/DashboardMarketPanels";
import { marketAPI } from "../../api/market";
import { analysisAPI } from "../../api/analysis";
import { paperAPI } from "../../api/paper";
import { zerodhaAPI } from "../../api/zerodha";
import { useSession } from "../../hooks/useMarket";
import { formatDateTime } from "../../utils/formatters";

const PRIMARY_ORDER = ["NIFTY", "NIFTY50", "BANKNIFTY"];
const CHART_INTERVALS = ["1m", "3m", "5m", "15m", "30m"];

function sortQuotes(quotes = []) {
    return [...quotes].sort((a, b) => {
        const aIdx = PRIMARY_ORDER.indexOf(a.symbol?.toUpperCase());
        const bIdx = PRIMARY_ORDER.indexOf(b.symbol?.toUpperCase());
        if (aIdx === -1 && bIdx === -1) return 0;
        if (aIdx === -1) return 1;
        if (bIdx === -1) return -1;
        return aIdx - bIdx;
    });
}

function sessionLabel(session) {
    if (session === "LIVE") return "Open";
    if (!session) return "Checking";
    return session.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function istDateParts(timestamp) {
    const parts = new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Kolkata",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
    }).formatToParts(new Date(timestamp));
    const values = Object.fromEntries(parts.map(({ type, value }) => [type, value]));
    return { year: Number(values.year), month: Number(values.month), day: Number(values.day) };
}

function getSessionBucketTime(timestamp, interval) {
    const { year, month, day } = istDateParts(timestamp);
    const utcWeekday = new Date(Date.UTC(year, month - 1, day)).getUTCDay();
    if (utcWeekday === 0 || utcWeekday === 6) return null;

    // NSE candles align to the 09:15 IST session open (including 30-minute
    // bars), not to midnight. 09:15 IST is 03:45 UTC.
    const sessionOpen = Date.UTC(year, month - 1, day, 3, 45);
    const sessionClose = Date.UTC(year, month - 1, day, 10, 0);
    if (timestamp < sessionOpen || timestamp >= sessionClose) return null;
    const intervalMs = Number.parseInt(interval, 10) * 60_000;
    const bucket = sessionOpen + Math.floor((timestamp - sessionOpen) / intervalMs) * intervalMs;
    return new Date(bucket).toISOString();
}

function mergeLiveCandle(history = [], liveCandle) {
    if (!liveCandle) return history;
    const existing = history.find((candle) => new Date(candle.candle_time).getTime() === new Date(liveCandle.candle_time).getTime());
    const nextLiveCandle = existing
        ? {
            ...existing,
            high: Math.max(Number(existing.high), liveCandle.high),
            low: Math.min(Number(existing.low), liveCandle.low),
            close: liveCandle.close,
            is_live: true,
        }
        : liveCandle;
    return [
        ...history.filter((candle) => new Date(candle.candle_time).getTime() !== new Date(liveCandle.candle_time).getTime()),
        nextLiveCandle,
    ].sort((a, b) => new Date(a.candle_time) - new Date(b.candle_time));
}

function StatusTile({ icon: Icon, label, value, detail, tone = "neutral" }) {
    const styles = {
        green: "border-green-200 bg-green-50 text-green-700",
        red: "border-red-200 bg-red-50 text-red-700",
        amber: "border-yellow-200 bg-yellow-50 text-yellow-700",
        blue: "border-blue-200 bg-blue-50 text-blue-700",
        neutral: "border-dark-700 bg-dark-900 text-dark-100",
    };

    return (
        <div className={`min-w-0 rounded-xl border px-4 py-3 shadow-sm ${styles[tone] || styles.neutral}`}>
            <div className="flex items-center justify-between gap-2">
                <p className="truncate text-[11px] font-bold uppercase tracking-[0.12em] opacity-75">{label}</p>
                <Icon className="h-4 w-4 shrink-0 opacity-80" aria-hidden="true" />
            </div>
            <p className="mt-2 truncate text-sm font-bold">{value}</p>
            <p className="mt-1 min-h-5 text-xs leading-5 opacity-80">{detail}</p>
        </div>
    );
}

function MarketTicker({ quote }) {
    const change = Number(quote.change_percent);
    const positive = Number.isFinite(change) && change >= 0;
    const DirectionIcon = positive ? ArrowUpRight : ArrowDownRight;

    return (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-dark-700 bg-dark-900 px-3 py-2.5">
            <div className="min-w-0">
                <p className="truncate text-xs font-semibold text-dark-500">{quote.symbol}</p>
                <p className="mt-0.5 font-mono text-base font-bold text-dark-100">
                    {Number(quote.ltp).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
            </div>
            <div className={`flex shrink-0 items-center gap-1 text-sm font-semibold ${positive ? "text-green-700" : "text-red-700"}`}>
                <DirectionIcon className="h-4 w-4" aria-hidden="true" />
                {Number.isFinite(change) ? `${Math.abs(change).toFixed(2)}%` : "—"}
            </div>
        </div>
    );
}

export default function Dashboard() {
    const [chartInterval, setChartInterval] = useState("5m");
    const [liveCandles, setLiveCandles] = useState({});
    const lastQuoteSampleRef = useRef(null);
    const { data: session, isError: sessionError } = useSession();
    const {
        data: quotes,
        isLoading: quotesLoading,
        isError: quotesError,
        dataUpdatedAt,
    } = useQuery({
        queryKey: ["quotes"],
        queryFn: () => marketAPI.getQuotes(),
        refetchInterval: 5000,
        select: (res) => res.data.data,
    });

    const { data: engineStatus, isLoading: engineStatusLoading } = useQuery({
        queryKey: ["market-engine-status"],
        queryFn: () => marketAPI.getEngineStatus(),
        refetchInterval: 30000,
        select: (res) => res.data.data,
    });
    const { data: brokerStatus, isLoading: brokerStatusLoading, isError: brokerStatusError } = useQuery({
        queryKey: ["zerodha-status"],
        queryFn: () => zerodhaAPI.getStatus(),
        refetchInterval: 30000,
        select: (res) => res.data.data,
    });
    const isMarketLive = session?.session === "LIVE";
    const {
        data: candleResult,
        isLoading: candlesLoading,
        isError: candlesError,
        isPlaceholderData: candlesArePreviousInterval,
    } = useQuery({
        queryKey: ["dashboard-candles", "NIFTY", chartInterval, isMarketLive],
        queryFn: async () => ({
            response: await marketAPI.getHistorical("NIFTY", {
                timeframe: chartInterval,
                limit: chartInterval === "1m" || chartInterval === "3m" ? 500 : 100,
                ...(isMarketLive ? { current_session: 1 } : {}),
            }),
            interval: chartInterval,
        }),
        refetchInterval: isMarketLive ? 30000 : false,
        placeholderData: keepPreviousData,
        select: ({ response, interval }) => ({
            candles: response.data.data,
            source: response.data.message,
            interval,
        }),
    });
    const { data: aiSignals } = useQuery({
        queryKey: ["ai-signals"],
        queryFn: () => analysisAPI.getSignals(),
        refetchInterval: 60000,
        select: (res) => res.data.data,
    });
    const { data: portfolio } = useQuery({
        queryKey: ["portfolio"],
        queryFn: () => paperAPI.getPortfolio(),
        refetchInterval: 30000,
        select: (res) => res.data.data,
    });
    const sortedQuotes = sortQuotes(quotes);
    const primaryQuote = sortedQuotes.find((quote) => ["NIFTY", "NIFTY50"].includes(quote.symbol?.toUpperCase()));
    const candles = candleResult?.candles || [];
    const liveCandle = liveCandles[chartInterval];
    const displayedInterval = candleResult?.interval || chartInterval;
    const chartLiveCandle = displayedInterval === chartInterval ? liveCandle : null;
    const chartCandles = mergeLiveCandle(candles, chartLiveCandle);
    const latestCandle = chartCandles.reduce((latest, candle) => (
        !latest || new Date(candle.candle_time) > new Date(latest.candle_time) ? candle : latest
    ), null);
    const todayInIndia = new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit",
    }).format(new Date());
    const historyIncludesToday = candles.some((candle) => (
        new Intl.DateTimeFormat("en-CA", {
            timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit",
        }).format(new Date(candle.candle_time)) === todayInIndia
    ));
    const latestStoredCandle = candles.reduce((latest, candle) => (
        !latest || new Date(candle.candle_time) > new Date(latest.candle_time) ? candle : latest
    ), null);
    const latestStoredCandleAgeMinutes = latestStoredCandle
        ? Math.max(0, (Date.now() - new Date(latestStoredCandle.candle_time).getTime()) / 60000)
        : null;
    const storedCandlesAreStale = latestStoredCandleAgeMinutes !== null
        && latestStoredCandleAgeMinutes > (isMarketLive ? 30 : 72 * 60);
    const liveCandleIsFromToday = Boolean(liveCandle && new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit",
    }).format(new Date(liveCandle.candle_time)) === todayInIndia);
    const hideOldChart = (storedCandlesAreStale && !liveCandleIsFromToday)
        || (isMarketLive && !historyIncludesToday && !liveCandle);
    const quoteAgeSeconds = dataUpdatedAt ? Math.max(0, Math.floor((Date.now() - dataUpdatedAt) / 1000)) : null;
    const quoteFeedIsFresh = !quotesError && quoteAgeSeconds !== null && quoteAgeSeconds <= 15;
    const quoteSync = quotesError
        ? "Latest request failed"
        : quoteAgeSeconds === null
            ? quotesLoading ? "Loading the first quote" : "Waiting for the first successful request"
            : quoteAgeSeconds > 30
                ? `Refresh delayed · last request ${quoteAgeSeconds}s ago`
                : `Request updated ${quoteAgeSeconds < 5 ? "just now" : `${quoteAgeSeconds}s ago`}`;
    const providerName = engineStatusLoading
        ? "Checking provider"
        : engineStatus?.provider?.toLowerCase() === "zerodha"
            ? "Zerodha configured"
            : engineStatus?.provider
                ? `${engineStatus.provider} configured`
                : "Provider unavailable";
    const brokerConnected = Boolean(brokerStatus?.is_connected && brokerStatus?.is_token_valid);
    const brokerLabel = brokerStatusError
        ? "Status unavailable"
        : brokerStatusLoading
            ? "Checking connection"
            : brokerConnected
            ? "Connected"
            : brokerStatus?.is_connected
                ? "Reconnect required"
                : "Not connected";

    useEffect(() => {
        const sampleTime = dataUpdatedAt;
        const price = Number(primaryQuote?.ltp);
        if (!isMarketLive || !sampleTime || !Number.isFinite(price) || price <= 0) return;
        if (Date.now() - sampleTime > 30_000 || lastQuoteSampleRef.current === sampleTime) return;

        lastQuoteSampleRef.current = sampleTime;
        setLiveCandles((previous) => {
            const next = { ...previous };
            CHART_INTERVALS.forEach((interval) => {
                const candleTime = getSessionBucketTime(sampleTime, interval);
                if (!candleTime) return;
                const current = previous[interval];
                if (current?.candle_time === candleTime) {
                    next[interval] = {
                        ...current,
                        high: Math.max(current.high, price),
                        low: Math.min(current.low, price),
                        close: price,
                    };
                } else {
                    next[interval] = {
                        candle_time: candleTime,
                        open: price,
                        high: price,
                        low: price,
                        close: price,
                        volume: 0,
                        is_live: true,
                    };
                }
            });
            return next;
        });
    }, [isMarketLive, dataUpdatedAt, primaryQuote?.ltp]);

    return (
        <PageWrapper title="Trading Overview" subtitle="Market context, signals, and account state in one view.">
            <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Trading system status">
                <StatusTile
                    icon={Activity}
                    label="Market session"
                    value={sessionError ? "Status unavailable" : sessionLabel(session?.session)}
                    detail={sessionError ? "Market-session request failed" : session?.session === "LIVE" ? "Market is open" : "Session state reported by Athena"}
                    tone={session?.session === "LIVE" ? "green" : "neutral"}
                />
                <StatusTile
                    icon={Radio}
                    label="Market data"
                    value={providerName}
                    detail={quoteSync}
                    tone={quotesError || (quoteAgeSeconds !== null && quoteAgeSeconds > 30) ? "amber" : "blue"}
                />
                <StatusTile
                    icon={brokerConnected ? ShieldCheck : ShieldAlert}
                    label="Zerodha connection"
                    value={brokerLabel}
                    detail={brokerStatusLoading
                        ? "Checking the saved Zerodha session"
                        : brokerConnected ? "Session token is valid" : "Check connection before using broker features"}
                    tone={brokerConnected ? "green" : brokerStatusError ? "amber" : "neutral"}
                />
                <StatusTile
                    icon={brokerStatus?.live_orders_enabled ? ShieldAlert : ShieldCheck}
                    label="Real-order permission"
                    value={brokerStatusLoading
                        ? "Checking server permission"
                        : brokerStatus?.live_orders_enabled === undefined
                            ? "Status unavailable"
                            : brokerStatus.live_orders_enabled ? "Enabled on server" : "Blocked on server"}
                    detail={brokerStatusLoading
                        ? "Reading the server order gate"
                        : brokerStatus?.live_orders_enabled === undefined
                            ? "Server permission has not been reported"
                            : brokerStatus.live_orders_enabled
                                ? "Server allows real-order requests"
                                : "Server currently rejects real-order requests"}
                    tone={brokerStatus?.live_orders_enabled ? "red" : brokerStatus?.live_orders_enabled === false ? "green" : "amber"}
                />
            </section>

            <section aria-label="Live market chart">
                <Card padding={false} className="overflow-hidden">
                    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-dark-700 px-5 py-4">
                        <div>
                            <p className="text-xs font-bold uppercase tracking-[0.16em] text-dark-500">NIFTY 50</p>
                            <p className="mt-1 text-sm text-dark-400">
                                {candlesArePreviousInterval
                                    ? `Loading ${chartInterval} candles · showing ${displayedInterval} temporarily`
                                    : `Latest session · ${displayedInterval.replace("m", "-minute")} candles`}
                            </p>
                        </div>
                        <div className="flex flex-wrap items-center justify-end gap-4">
                            <Select
                                label="Candle interval"
                                aria-label="Candle interval"
                                value={chartInterval}
                                onChange={(event) => setChartInterval(event.target.value)}
                                options={CHART_INTERVALS.map((interval) => ({ value: interval, label: interval }))}
                                className="w-32 text-left"
                            />
                            {liveCandle && (
                                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${isMarketLive && quoteFeedIsFresh ? "bg-green-500/15 text-green-300" : "bg-dark-800 text-dark-400"}`}>
                                    {isMarketLive && quoteFeedIsFresh ? "Live candle" : "Last candle"}
                                </span>
                            )}
                            <div className="text-right">
                                <p className="font-mono text-2xl font-bold tracking-tight text-dark-50">
                                    {primaryQuote?.ltp !== undefined
                                        ? Number(primaryQuote.ltp).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                                        : "—"}
                                </p>
                                <p className={`mt-1 text-sm font-semibold ${Number(primaryQuote?.change_percent) >= 0 ? "text-green-700" : "text-red-700"}`}>
                                    {quotesLoading
                                        ? "Loading quote…"
                                        : primaryQuote?.change_percent !== undefined
                                        ? `${Number(primaryQuote.change_percent) >= 0 ? "▲" : "▼"} ${Math.abs(Number(primaryQuote.change_percent)).toFixed(2)}% today`
                                        : "Quote unavailable"}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="px-3 pb-3 pt-2 sm:px-5">
                        {candlesLoading ? <Spinner text="Loading candles…" /> : candlesError ? (
                            <div className="flex min-h-64 items-center justify-center rounded-lg bg-dark-950 px-5 text-center text-sm text-dark-500">
                                Candle history could not be loaded. Check the market-data provider.
                            </div>
                        ) : (
                            <>
                                {hideOldChart ? (
                                    <div className="flex min-h-64 flex-col items-center justify-center gap-2 rounded-lg border border-dark-700 bg-dark-950 px-5 text-center" role="status">
                                        <p className="text-sm font-semibold text-dark-200">
                                            {latestStoredCandle ? "Old candles hidden" : "Waiting for today’s candles"}
                                        </p>
                                        <p className="max-w-xl text-xs leading-5 text-dark-400">
                                            {isMarketLive
                                                ? "Today’s history hasn’t arrived yet. The chart will appear when Zerodha history or a fresh NIFTY quote is available."
                                                : "No recent candles are stored for this interval. It will refresh from Zerodha when the market opens; older candles are kept but hidden here."}
                                        </p>
                                        {latestStoredCandle && (
                                            <p className="text-xs text-dark-500">Last stored {chartInterval.replace("m", "-minute")} candle: {formatDateTime(latestStoredCandle.candle_time)}</p>
                                        )}
                                    </div>
                                ) : isMarketLive && liveCandle && !quoteFeedIsFresh ? (
                                    <p className="mb-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs leading-5 text-amber-200" role="status">
                                        The quote feed is delayed. Showing the last {chartInterval.replace("m", "-minute")} candle received at {formatDateTime(liveCandle.candle_time)} until quotes resume.
                                    </p>
                                ) : liveCandleIsFromToday && liveCandle && !historyIncludesToday ? (
                                    <p className="mb-2 rounded-md border border-blue-500/30 bg-blue-500/10 px-3 py-2 text-xs leading-5 text-blue-200" role="status">
                                        Earlier candles for today aren’t available from Zerodha yet; this chart contains quote data collected since this page opened.
                                    </p>
                                ) : null}
                                {!hideOldChart && isMarketLive && liveCandle && historyIncludesToday && (
                                    <p className="mb-2 rounded-md border border-green-500/30 bg-green-500/10 px-3 py-2 text-xs leading-5 text-green-200" role="status">
                                        Quotes refresh every 5 seconds; history refreshes every 30 seconds while the market is open.
                                    </p>
                                )}
                                {!hideOldChart && <CandleChart candles={chartCandles} currentPrice={primaryQuote?.ltp} interval={displayedInterval} />}
                            </>
                        )}
                        <div className="mt-2 flex flex-wrap items-center justify-between gap-2 border-t border-dark-800 pt-3 text-xs text-dark-500">
                            <span className="inline-flex items-center gap-2"><Clock3 className="h-3.5 w-3.5" aria-hidden="true" />{candleResult?.source && candleResult.source !== "Success"
                                ? `${candleResult.source.replace(/\.$/, "")} · `
                                : liveCandle
                                    ? `${isMarketLive ? "Live quote candle" : "Last quote candle"} + stored history · `
                                    : "Stored history · "}candle data through {latestCandle ? formatDateTime(latestCandle.candle_time) : "unavailable"}</span>
                            <a href="/market/option-chain" className="inline-flex items-center gap-1 font-semibold text-primary-600 hover:text-primary-700">
                                Open option chain <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                            </a>
                        </div>
                    </div>
                </Card>

            </section>

            <DashboardMarketPanels brokerStatus={brokerStatus} aiSignals={aiSignals || []} quote={primaryQuote} marketIsLive={isMarketLive} quoteFeedIsFresh={quoteFeedIsFresh} />

            <section className="grid grid-cols-1 gap-4 xl:grid-cols-2" aria-label="Additional market and account context">
                <Card title="Market watch" subtitle="Indices from the configured market provider">
                    <div className="space-y-2">
                        {sortedQuotes.slice(0, 4).map((quote) => <MarketTicker key={quote.symbol} quote={quote} />)}
                        {!quotesLoading && !sortedQuotes.length && (
                            <p className="rounded-lg bg-dark-950 px-3 py-4 text-sm text-dark-500">No quote data is available. Check the provider and instrument list.</p>
                        )}
                    </div>
                </Card>
                <PortfolioCard portfolio={portfolio} />
            </section>

            <section className="grid grid-cols-1 gap-4">
                <AISignalCard signals={aiSignals || []} />
            </section>
        </PageWrapper>
    );
}
