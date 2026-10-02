import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, RefreshCw } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Alert, Badge, Button, Card, Select, Spinner } from "../../components/common";
import OptionChainTable from "./components/OptionChainTable";
import MarketReadPanel from "./components/MarketReadPanel";
import { marketAPI } from "../../api/market";
import { INDICES } from "../../utils/constants";
import { formatNumber } from "../../utils/formatters";

const WINDOWS = [
    { value: "5", label: "ATM ± 5 strikes" },
    { value: "10", label: "ATM ± 10 strikes" },
    { value: "all", label: "All available strikes" },
];

function Metric({ label, value, detail }) {
    return (
        <div className="rounded-xl border border-dark-700 bg-dark-900 px-4 py-3">
            <p className="text-xs font-medium text-dark-300">{label}</p>
            <p className="mt-1 text-lg font-semibold text-dark-50">{value}</p>
            {detail && <p className="mt-0.5 text-xs text-dark-300">{detail}</p>}
        </div>
    );
}

function displayRatio(value) {
    return value === null || value === undefined || !Number.isFinite(Number(value))
        ? "—"
        : Number(value).toFixed(2);
}

function indiaToday() {
    const parts = new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Kolkata",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
    }).formatToParts(new Date());
    const datePart = (type) => parts.find((part) => part.type === type)?.value;
    return `${datePart("year")}-${datePart("month")}-${datePart("day")}`;
}

export default function OptionChain() {
    const [symbol, setSymbol] = useState("NIFTY");
    const [expiry, setExpiry] = useState("");
    const [strikeWindow, setStrikeWindow] = useState("5");
    const [showGreeks, setShowGreeks] = useState(false);

    const expiriesQuery = useQuery({
        queryKey: ["option-expiries", symbol],
        queryFn: () => marketAPI.getExpiry(symbol),
        select: (res) => res.data.data ?? [],
        staleTime: 60_000,
    });
    const allExpiries = expiriesQuery.data ?? [];
    const today = indiaToday();
    const expiries = allExpiries.filter((item) => item.expiry >= today);

    useEffect(() => {
        const values = expiries.map((item) => item.expiry);
        if (!values.includes(expiry)) setExpiry(values[0] ?? "");
    }, [expiries, expiry]);

    const params = useMemo(() => (expiry ? { expiry } : undefined), [expiry]);
    const engineQuery = useQuery({
        queryKey: ["market-engine-status"],
        queryFn: marketAPI.getEngineStatus,
        select: (res) => res.data.data ?? null,
        staleTime: 30_000,
        refetchInterval: 60_000,
    });
    const chainQuery = useQuery({
        queryKey: ["option-chain", symbol, expiry],
        queryFn: () => marketAPI.getOptionChain(symbol, params),
        enabled: Boolean(expiry),
        select: (res) => ({ rows: res.data.data ?? [], message: res.data.message }),
        refetchInterval: () => engineQuery.data?.provider === "zerodha" && engineQuery.data?.is_live ? 15_000 : false,
    });
    const summaryQuery = useQuery({
        queryKey: ["option-chain-summary", symbol, expiry],
        queryFn: () => marketAPI.getOptionChainSummary(symbol, params),
        enabled: Boolean(expiry),
        select: (res) => res.data.data ?? null,
        refetchInterval: () => engineQuery.data?.provider === "zerodha" && engineQuery.data?.is_live ? 30_000 : false,
    });
    const marketReadQuery = useQuery({
        queryKey: ["market-read", symbol],
        queryFn: () => marketAPI.getMarketRead(symbol),
        select: (res) => res.data.data ?? null,
        staleTime: 30_000,
        refetchInterval: () => engineQuery.data?.provider === "zerodha" && engineQuery.data?.is_live ? 30_000 : false,
    });

    const chain = chainQuery.data?.rows ?? [];
    const summary = summaryQuery.data;
    const sortedStrikes = useMemo(
        () => [...new Set(chain.map((row) => Number(row.strike)))].sort((a, b) => a - b),
        [chain],
    );
    const visibleStrikes = useMemo(() => {
        if (strikeWindow === "all" || !sortedStrikes.length) return sortedStrikes;
        const reference = summary?.atm_strike ?? summary?.spot_price;
        if (reference === null || reference === undefined) return sortedStrikes;
        let atmIndex = 0;
        sortedStrikes.forEach((strike, index) => {
            if (Math.abs(strike - reference) < Math.abs(sortedStrikes[atmIndex] - reference)) atmIndex = index;
        });
        const radius = Number(strikeWindow);
        return sortedStrikes.slice(Math.max(0, atmIndex - radius), atmIndex + radius + 1);
    }, [sortedStrikes, strikeWindow, summary]);

    const refresh = () => {
        expiriesQuery.refetch();
        if (expiry) {
            chainQuery.refetch();
            summaryQuery.refetch();
        }
        engineQuery.refetch();
        marketReadQuery.refetch();
    };
    const provider = engineQuery.data?.provider;
    const isMock = provider === "mock";
    const providerLabel = engineQuery.isPending
        ? "Checking"
        : engineQuery.isError
            ? "Unavailable"
            : provider === "zerodha"
                ? "Zerodha"
                : provider === "mock"
                    ? "Mock"
                    : "Unknown";
    const refreshDescription = engineQuery.isPending
        ? "Checking market-data status…"
        : engineQuery.isError
            ? "Status unavailable · refresh manually"
            : provider !== "zerodha"
                ? "Manual refresh · mock provider has no live chain"
                : engineQuery.data?.is_live
                    ? "Auto-refreshes during market hours"
                    : "Market closed · refresh manually";
    const error = chainQuery.isError || summaryQuery.isError || expiriesQuery.isError;
    const hasExpiry = Boolean(expiry);
    const emptyMessage = chainQuery.isError
        ? (chainQuery.error?.response?.data?.message ?? "Unable to fetch option quotes. Check the Zerodha connection and quote access.")
        : isMock
            ? "The mock provider does not supply option-chain quotes. Configure Zerodha market data to view actual quotes."
            : chainQuery.data?.message && chainQuery.data.message !== "Success"
                ? chainQuery.data.message
                : "No option quotes were returned. Check the instrument catalog and market-data connection.";
    const updatedAt = chainQuery.dataUpdatedAt
        ? new Date(chainQuery.dataUpdatedAt).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
        : "Not loaded";

    return (
        <PageWrapper
            title="Options Workspace"
            subtitle="Explore the selected expiry, strikes, and chain analytics. Read-only market data; no order actions are available here."
            actions={
                <Button variant="secondary" size="sm" icon={RefreshCw} loading={chainQuery.isFetching || summaryQuery.isFetching} onClick={refresh}>
                    Refresh
                </Button>
            }
        >
            <Alert type="info" title="Read-only workspace" message="Viewing option data does not enable live trading or place orders." />

            <Card className="!p-4">
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                    <Select label="Underlying" options={INDICES.map((item) => ({ value: item, label: item }))} value={symbol} onChange={(event) => { setSymbol(event.target.value); setExpiry(""); }} />
                    <Select
                        label="Expiry"
                        options={expiries.map((item) => ({ value: item.expiry, label: new Date(`${item.expiry}T00:00:00`).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) }))}
                        value={expiry}
                        onChange={(event) => setExpiry(event.target.value)}
                        disabled={!expiries.length || expiriesQuery.isLoading}
                    />
                    <Select label="Strike range" options={WINDOWS} value={strikeWindow} onChange={(event) => setStrikeWindow(event.target.value)} />
                    <div className="flex flex-col justify-end gap-2 pb-1">
                        <div className="flex items-center gap-2">
                            <Activity className="h-4 w-4 text-dark-400" />
                            <span className="text-xs text-dark-400">Data provider</span>
                            <Badge variant={provider === "zerodha" ? "green" : provider === "mock" ? "yellow" : "gray"}>{providerLabel}</Badge>
                        </div>
                        <p className="text-xs text-dark-400">Updated {updatedAt} · {refreshDescription}</p>
                    </div>
                </div>
            </Card>

            {error && (
                <Alert type="error" title="Some data could not be loaded" message="Refresh to retry. If this continues, check the market-data provider and instrument list." />
            )}

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                <Metric label="Spot price" value={formatNumber(summary?.spot_price)} detail={symbol} />
                <Metric label="ATM strike" value={formatNumber(summary?.atm_strike, 0)} detail={expiry || "Select an expiry"} />
                <Metric label="Put / call OI" value={displayRatio(summary?.pcr_oi)} detail="PCR by open interest" />
                <Metric label="Put / call volume" value={displayRatio(summary?.pcr_volume)} detail="PCR by traded volume" />
                <Metric label="Max pain" value={formatNumber(summary?.max_pain, 0)} detail="For selected expiry" />
            </div>

            <MarketReadPanel
                symbol={symbol}
                expiry={expiry}
                summary={summary}
                chain={chain}
                chainFetchedAt={chainQuery.dataUpdatedAt}
                snapshot={marketReadQuery.data}
                isLoading={marketReadQuery.isLoading}
                isError={marketReadQuery.isError}
            />

            <Card title="Option chain" subtitle={`${symbol}${expiry ? ` · Expiry ${expiry}` : " · Choose an available expiry"}`} padding={false}>
                {chainQuery.isLoading || expiriesQuery.isLoading ? (
                    <div className="p-10"><Spinner text="Loading option-chain data..." /></div>
                ) : expiriesQuery.isError ? (
                    <div className="p-8 text-center">
                        <p className="font-medium text-dark-200">Expiry dates could not be loaded</p>
                        <p className="mt-1 text-sm text-dark-400">Refresh to retry the instrument catalog request.</p>
                    </div>
                ) : !hasExpiry ? (
                    <div className="p-8 text-center">
                        <p className="font-medium text-dark-200">No upcoming expiry dates available</p>
                        <p className="mt-1 text-sm text-dark-400">
                            {allExpiries.length
                                ? `Expired contracts are hidden. Refresh the NFO instrument list to load upcoming ${symbol} expiries.`
                                : `Check that NFO instruments are imported for ${symbol} and the selected provider can access market data.`}
                        </p>
                    </div>
                ) : !chain.length ? (
                    <div className="p-8 text-center">
                        <p className="font-medium text-dark-200">No option-chain quotes returned</p>
                        <p className="mt-1 text-sm text-dark-400">{emptyMessage}</p>
                        {engineQuery.data?.session === "CLOSED" && !isMock && (
                            <p className="mt-1 text-sm text-dark-400">The scheduled market session is closed. Quotes may be from the last session; verify fresh prices during market hours.</p>
                        )}
                    </div>
                ) : (
                    <>
                        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-dark-700/70 px-4 py-3">
                            <div className="text-xs text-dark-400">
                                <span>{visibleStrikes.length} of {sortedStrikes.length} strikes · ATM row highlighted</span>
                                <span className="ml-2">PCR and max pain describe this expiry; they are not forecasts.</span>
                            </div>
                            <label className="flex cursor-pointer items-center gap-2 text-xs text-dark-300">
                                <input type="checkbox" className="accent-fuchsia-400" checked={showGreeks} onChange={(event) => setShowGreeks(event.target.checked)} />
                                Show Greeks
                            </label>
                        </div>
                        <OptionChainTable chain={chain} strikes={visibleStrikes} atmStrike={summary?.atm_strike} showGreeks={showGreeks} />
                    </>
                )}
            </Card>
        </PageWrapper>
    );
}
