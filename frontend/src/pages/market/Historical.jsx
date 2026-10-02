import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Alert, Card, Select, Input, Button, Spinner } from "../../components/common";
import { marketAPI } from "../../api/market";
import { useSession } from "../../hooks/useMarket";
import { INDICES, TIMEFRAMES } from "../../utils/constants";
import { formatNumber, formatDate, formatDateTime, formatRelativeTime } from "../../utils/formatters";

export default function Historical() {
    const [symbol, setSymbol] = useState("NIFTY");
    const [timeframe, setTimeframe] = useState("15m");
    const [limit, setLimit] = useState(100);
    const { data: session } = useSession();
    const isMarketLive = session?.session === "LIVE";
    const isIntraday = !["1h", "1d"].includes(timeframe);
    const futuresQuery = useQuery({
        queryKey: ["nifty-futures-activity"],
        queryFn: () => marketAPI.getFuturesActivity("NIFTY"),
        select: (res) => res.data.data,
        enabled: symbol === "NIFTY",
        refetchInterval: isMarketLive ? 15000 : false,
    });

    const { data, isLoading, isError, refetch, isFetching } = useQuery({
        queryKey: ["historical", symbol, timeframe, limit, isMarketLive],
        queryFn: () => marketAPI.getHistorical(symbol, {
            timeframe,
            limit,
            ...(isMarketLive && isIntraday ? { current_session: 1 } : {}),
        }),
        select: (res) => ({ candles: res.data.data || [], message: res.data.message || "" }),
        enabled: !!symbol,
    });
    const candles = data?.candles || [];
    const futures = futuresQuery.data;
    const quoteTimestamp = futures?.quote_timestamp;
    const quoteAgeSeconds = quoteTimestamp
        ? Math.max(0, Math.floor((Date.now() - new Date(quoteTimestamp).getTime()) / 1000))
        : null;
    const futuresQuoteIsFresh = quoteAgeSeconds !== null && quoteAgeSeconds <= 30;

    const columns = ["Time", "Open", "High", "Low", "Close", "Volume"];

    return (
        <PageWrapper
            title="Historical Data"
            subtitle="Historical OHLC candles from Athena’s configured market-data provider"
            actions={
                <div className="flex items-center gap-2">
                    <Select
                        options={INDICES.map((i) => ({ value: i, label: i }))}
                        value={symbol}
                        onChange={(e) => setSymbol(e.target.value)}
                        className="w-36"
                    />
                    <Select
                        options={TIMEFRAMES}
                        value={timeframe}
                        onChange={(e) => setTimeframe(e.target.value)}
                        className="w-28"
                    />
                    <Input
                        type="number"
                        value={limit}
                        onChange={(e) => setLimit(e.target.value)}
                        className="w-24"
                        placeholder="Limit"
                    />
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={() => refetch()}
                        loading={isFetching}
                    >
                        Load
                    </Button>
                </div>
            }
        >
            {symbol === "NIFTY" && (
                <Card
                    title="NIFTY Futures Activity"
                    subtitle="Nearest active NIFTY futures contract · separate from NIFTY spot candles"
                >
                    {futuresQuery.isLoading ? (
                        <Spinner text="Loading futures quote…" />
                    ) : futuresQuery.isError ? (
                        <Alert
                            type="error"
                            title="Futures activity unavailable"
                            message="Athena could not retrieve the NIFTY futures quote. The spot candles below are unaffected."
                        />
                    ) : !futures?.available ? (
                        <p className="text-sm text-dark-400">
                            {futures?.reason || "NIFTY futures data is unavailable from the configured provider."}
                        </p>
                    ) : (
                        <div>
                            <div className="flex flex-wrap items-center justify-between gap-3">
                                <div>
                                    <p className="font-mono text-sm font-semibold text-dark-100">{futures.trading_symbol}</p>
                                    <p className="mt-1 text-xs text-dark-400">
                                        Expiry {formatDate(futures.expiry)}
                                        {" · "}Source {futures.source}
                                    </p>
                                </div>
                                <div className={"text-xs font-semibold " + (quoteAgeSeconds === null ? "text-dark-400" : isMarketLive ? futuresQuoteIsFresh ? "text-green-300" : "text-amber-300" : "text-dark-400")}>
                                    {quoteAgeSeconds === null
                                        ? "Quote freshness unavailable"
                                        : isMarketLive && !futuresQuoteIsFresh
                                            ? "Delayed · quote " + formatRelativeTime(quoteTimestamp)
                                            : isMarketLive
                                                ? "Quote updated " + formatRelativeTime(quoteTimestamp)
                                                : "Last quote " + formatRelativeTime(quoteTimestamp)}
                                </div>
                            </div>
                            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
                                <div className="rounded-lg border border-dark-700 bg-dark-900 px-3 py-3">
                                    <p className="text-xs text-dark-500">Futures LTP</p>
                                    <p className="mt-1 font-mono text-lg font-semibold text-dark-100">{formatNumber(futures.ltp)}</p>
                                </div>
                                <div className="rounded-lg border border-dark-700 bg-dark-900 px-3 py-3">
                                    <p className="text-xs text-dark-500">Today’s futures volume</p>
                                    <p className="mt-1 font-mono text-lg font-semibold text-dark-100">
                                        {futures.volume === null || futures.volume === undefined
                                            ? "Unavailable"
                                            : Number(futures.volume).toLocaleString("en-IN")}
                                    </p>
                                </div>
                                <div className="rounded-lg border border-dark-700 bg-dark-900 px-3 py-3">
                                    <p className="text-xs text-dark-500">Futures session VWAP</p>
                                    <p className="mt-1 font-mono text-lg font-semibold text-dark-100">{formatNumber(futures.vwap)}</p>
                                </div>
                            </div>
                            {futures.last_trade_time && (
                                <p className="mt-3 text-xs text-dark-500">
                                    Last futures trade {formatRelativeTime(futures.last_trade_time)}
                                    {" · "}quote snapshot {formatDateTime(quoteTimestamp)}
                                </p>
                            )}
                            {futures.reason && (
                                <p className="mt-3 text-xs text-dark-400">{futures.reason}</p>
                            )}
                            <p className="mt-3 text-xs text-dark-500">
                                Volume is the contract’s cumulative session volume. VWAP is Zerodha’s futures average price; neither is NIFTY spot volume or spot VWAP.
                            </p>
                        </div>
                    )}
                </Card>
            )}
            <Card padding={false}>
                {isLoading ? (
                    <Spinner text="Loading candles..." />
                ) : isError ? (
                    <div className="p-4">
                        <Alert
                            type="error"
                            title="Could not load historical data"
                            message="Athena could not retrieve candles from the configured provider. Check the connection and retry."
                        />
                    </div>
                ) : (
                    <div>
                        {isMarketLive && isIntraday && data?.message && (
                            <div className="p-4 pb-0">
                                <Alert type="info" message={`${data.message} The current interval may still be forming.`} />
                            </div>
                        )}
                        {candles.length > 0 && candles.every((c) => Number(c.volume) <= 0) && (
                            <p className="px-4 pt-3 text-xs text-dark-400" role="note">
                                {symbol} is an index and has no directly traded volume. Zerodha reports zero for index candles, so the table shows N/A. Check related futures or options volume for traded activity.
                            </p>
                        )}
                        <div className="overflow-x-auto">
                            <table className="table text-xs">
                                <thead>
                                    <tr>
                                        {columns.map((col) => (
                                            <th key={col}>{col}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {candles.map((c, i) => (
                                        <tr key={`${c.candle_time}-${i}`}>
                                            <td className="font-mono text-dark-400">
                                                {formatDateTime(c.candle_time)}
                                            </td>
                                            <td className="font-mono">{formatNumber(c.open)}</td>
                                            <td className="font-mono text-green-400">
                                                {formatNumber(c.high)}
                                            </td>
                                            <td className="font-mono text-red-400">
                                                {formatNumber(c.low)}
                                            </td>
                                            <td className="font-mono font-semibold">
                                                {formatNumber(c.close)}
                                            </td>
                                            <td className="font-mono text-dark-400">
                                                {Number(c.volume) > 0 ? Number(c.volume).toLocaleString("en-IN") : "N/A"}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {candles.length === 0 && (
                                <p className="p-6 text-center text-sm text-dark-400">No candles are available for this symbol and interval.</p>
                            )}
                        </div>
                    </div>
                )}
            </Card>
        </PageWrapper>
    );
}
