import { useQuery } from "@tanstack/react-query";
import { ArrowDownRight, ArrowUpRight, RefreshCw } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Alert, Badge, Button, Card, Spinner } from "../../components/common";
import { marketAPI } from "../../api/market";
import { useSession } from "../../hooks/useMarket";
import {
    formatDateTime,
    formatNumber,
    formatPercent,
    formatRelativeTime,
} from "../../utils/formatters";

const SYMBOL_ORDER = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"];

function sortQuotes(quotes = []) {
    return [...quotes].sort((a, b) => {
        const aIndex = SYMBOL_ORDER.indexOf(a.symbol?.toUpperCase());
        const bIndex = SYMBOL_ORDER.indexOf(b.symbol?.toUpperCase());
        if (aIndex === -1 && bIndex === -1) return (a.symbol || "").localeCompare(b.symbol || "");
        if (aIndex === -1) return 1;
        if (bIndex === -1) return -1;
        return aIndex - bIndex;
    });
}

function QuoteCard({ quote }) {
    const change = Number(quote.change_percent);
    const positive = change > 0;
    const negative = change < 0;
    const Icon = positive ? ArrowUpRight : ArrowDownRight;
    const tone = positive ? "text-emerald-300" : negative ? "text-rose-300" : "text-dark-300";

    return (
        <Card className="h-full">
            <div className="flex items-start justify-between gap-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-dark-400">
                        {quote.symbol}
                    </p>
                    <p className="mt-2 font-mono text-2xl font-semibold text-dark-50">
                        {formatNumber(quote.ltp)}
                    </p>
                </div>
                <div
                    className={`inline-flex items-center gap-1 rounded-full border border-dark-700 px-2.5 py-1 text-sm font-medium ${tone}`}
                >
                    {positive || negative ? <Icon className="h-4 w-4" /> : null}
                    {formatPercent(quote.change_percent)}
                </div>
            </div>

            <p className={`mt-1 text-sm ${tone}`}>
                {quote.change > 0 ? "+" : ""}
                {formatNumber(quote.change)} today
            </p>

            <div className="mt-5 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-dark-700/80 pt-4 text-xs">
                <QuoteStat label="Open" value={quote.open} />
                <QuoteStat label="Previous close" value={quote.close} />
                <QuoteStat label="Day high" value={quote.high} />
                <QuoteStat label="Day low" value={quote.low} />
                <div>
                    <p className="text-dark-500">Volume</p>
                    <p className="mt-1 font-mono text-dark-300">
                        {Number(quote.volume) > 0
                            ? Number(quote.volume).toLocaleString("en-IN")
                            : "Unavailable"}
                    </p>
                </div>
                <div>
                    <p className="text-dark-500">Last trade</p>
                    <p
                        className="mt-1 text-dark-300"
                        title={quote.timestamp ? formatDateTime(quote.timestamp) : undefined}
                    >
                        {quote.timestamp
                            ? formatRelativeTime(quote.timestamp)
                            : "Timestamp unavailable"}
                    </p>
                </div>
            </div>
        </Card>
    );
}

function QuoteStat({ label, value }) {
    return (
        <div>
            <p className="text-dark-500">{label}</p>
            <p className="mt-1 font-mono text-dark-300">{formatNumber(value)}</p>
        </div>
    );
}

export default function MarketWatch() {
    const sessionQuery = useSession();
    const quotesQuery = useQuery({
        queryKey: ["quotes"],
        queryFn: () => marketAPI.getQuotes(),
        refetchInterval: 5000,
        select: (response) => response.data.data || [],
    });
    const statusQuery = useQuery({
        queryKey: ["market-engine-status"],
        queryFn: () => marketAPI.getEngineStatus(),
        refetchInterval: 30000,
        select: (response) => response.data.data,
    });

    const quotes = sortQuotes(quotesQuery.data);
    const isMarketOpen = sessionQuery.data?.session === "LIVE";

    return (
        <PageWrapper
            title="Market Watch"
            subtitle="Live index quotes from your configured market-data provider"
            actions={
                <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => quotesQuery.refetch()}
                    disabled={quotesQuery.isFetching}
                >
                    <RefreshCw
                        className={`mr-2 h-4 w-4 ${quotesQuery.isFetching ? "animate-spin" : ""}`}
                    />
                    Refresh
                </Button>
            }
        >
            <div className="flex flex-wrap items-center gap-2 text-sm">
                <Badge variant={isMarketOpen ? "green" : "gray"}>
                    {sessionQuery.isLoading
                        ? "Checking market session"
                        : isMarketOpen
                          ? "Market open"
                          : "Market closed"}
                </Badge>
                <span className="text-dark-400">
                    Provider:{" "}
                    {statusQuery.data?.provider === "zerodha"
                        ? "Zerodha"
                        : statusQuery.data?.provider || "Checking"}
                </span>
                <span className="text-dark-500">·</span>
                <span className="text-dark-400">
                    {quotesQuery.dataUpdatedAt
                        ? `Quotes refreshed ${formatRelativeTime(quotesQuery.dataUpdatedAt)} · auto-refreshes every 5 seconds`
                        : "Waiting for first quote update"}
                </span>
            </div>

            {quotesQuery.isError ? (
                <Alert
                    type="error"
                    title="Market quotes unavailable"
                    message="Athena could not refresh quotes from the configured provider. Check the Market Data status and Zerodha connection, then retry."
                />
            ) : quotesQuery.isLoading ? (
                <Card>
                    <Spinner text="Loading live market quotes…" />
                </Card>
            ) : quotes.length ? (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {quotes.map((quote) => (
                        <QuoteCard key={quote.symbol} quote={quote} />
                    ))}
                </div>
            ) : (
                <Card>
                    <p className="font-medium text-dark-200">No quotes available</p>
                    <p className="mt-1 text-sm text-dark-400">
                        The configured provider returned no index quotes. Try refreshing or check
                        its connection.
                    </p>
                </Card>
            )}
        </PageWrapper>
    );
}
