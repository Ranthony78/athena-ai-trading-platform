import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BriefcaseBusiness, ShieldAlert, ShieldCheck, TriangleAlert } from "lucide-react";
import {
    Alert,
    Badge,
    Button,
    Card,
    Input,
    Modal,
    Select,
    Spinner,
} from "../../../components/common";
import { marketAPI } from "../../../api/market";
import { zerodhaAPI } from "../../../api/zerodha";
import { formatCurrency, formatDateTime } from "../../../utils/formatters";

const fmt = (value, digits = 2) =>
    value == null || !Number.isFinite(Number(value))
        ? "—"
        : Number(value).toLocaleString("en-IN", {
              maximumFractionDigits: digits,
              minimumFractionDigits: digits,
          });
const nearestExpiry = (items = []) =>
    items.find((item) => item.expiry >= new Date().toISOString().slice(0, 10))?.expiry || "";

function DataValue({ label, value, detail }) {
    return (
        <div className="rounded-lg border border-dark-700 bg-dark-900/50 p-3">
            <p className="text-xs text-dark-400">{label}</p>
            <p className="mt-1 text-lg font-semibold text-dark-100">{value ?? "Unavailable"}</p>
            {detail && <p className="mt-1 text-xs leading-5 text-dark-500">{detail}</p>}
        </div>
    );
}

function EvidenceChip({ label, value, note }) {
    return (
        <div className="rounded-lg border border-dark-700 bg-dark-900/50 p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-dark-400">
                {label}
            </p>
            <p className="mt-2 text-sm font-semibold text-dark-100">{value || "Unavailable"}</p>
            {note && <p className="mt-1 text-xs text-dark-500">{note}</p>}
        </div>
    );
}

function LiveOrderReview({
    open,
    onClose,
    contract,
    brokerStatus,
    marketIsLive,
    quoteFeedIsFresh,
    chainIsFresh,
    onPlace,
    placing,
}) {
    const lotSize = Math.max(1, Number(contract?.lot_size) || 1);
    const [quantity, setQuantity] = useState(String(lotSize));
    const [orderType, setOrderType] = useState("LIMIT");
    const [price, setPrice] = useState(contract?.ltp ? String(contract.ltp) : "");
    const [acknowledged, setAcknowledged] = useState(false);
    useEffect(() => {
        if (open) {
            setQuantity(String(lotSize));
            setPrice(contract?.ltp ? String(contract.ltp) : "");
            setOrderType("LIMIT");
            setAcknowledged(false);
        }
    }, [open, lotSize, contract?.ltp]);
    const qty = Number(quantity);
    const orderPrice = Number(price);
    const valid =
        Number.isInteger(qty) &&
        qty >= lotSize &&
        qty % lotSize === 0 &&
        (orderType === "MARKET" || (Number.isFinite(orderPrice) && orderPrice > 0));
    const canPlace =
        valid &&
        acknowledged &&
        marketIsLive &&
        quoteFeedIsFresh &&
        chainIsFresh &&
        brokerStatus?.is_connected &&
        brokerStatus?.is_token_valid &&
        brokerStatus?.live_orders_enabled;

    return (
        <Modal isOpen={open} onClose={onClose} title="Review live Zerodha order" size="md">
            <div className="space-y-4">
                <div className="rounded-lg border border-red-400/30 bg-red-950/25 p-3 text-sm text-red-200">
                    <p className="font-semibold">This submits a real order to Zerodha.</p>
                    <p className="mt-1 text-xs leading-5 text-red-200/80">
                        Review every field. Athena will not submit until you confirm below. A zero
                        balance does not guarantee an order will be rejected.
                    </p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                        <p className="text-xs text-dark-500">AI-selected contract</p>
                        <p className="mt-1 font-mono text-dark-100">
                            {contract?.trading_symbol || "—"}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-dark-500">Side / exchange</p>
                        <p className="mt-1 text-dark-100">BUY · NFO</p>
                    </div>
                    <div>
                        <p className="text-xs text-dark-500">Expiry · strike</p>
                        <p className="mt-1 text-dark-100">
                            {contract?.expiry || "—"} · {fmt(contract?.strike, 0)}{" "}
                            {contract?.option_type}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-dark-500">Current premium</p>
                        <p className="mt-1 font-mono text-dark-100">₹{fmt(contract?.ltp)}</p>
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                    <Input
                        label={`Quantity (lot size ${lotSize})`}
                        type="number"
                        min={lotSize}
                        step={lotSize}
                        value={quantity}
                        onChange={(event) => setQuantity(event.target.value)}
                    />
                    <Select
                        label="Order type"
                        value={orderType}
                        onChange={(event) => setOrderType(event.target.value)}
                        options={[
                            { value: "LIMIT", label: "Limit" },
                            { value: "MARKET", label: "Market" },
                        ]}
                    />
                    {orderType === "LIMIT" && (
                        <Input
                            label="Limit premium (₹)"
                            type="number"
                            min="0.05"
                            step="0.05"
                            value={price}
                            onChange={(event) => setPrice(event.target.value)}
                        />
                    )}
                    <Select
                        label="Product"
                        value="NRML"
                        disabled
                        options={[{ value: "NRML", label: "NRML · carry forward" }]}
                    />
                </div>
                {qty > 0 && Number.isInteger(qty) && Number(contract?.ltp) > 0 && (
                    <p className="text-xs text-dark-400">
                        Indicative premium value: ₹{fmt(qty * Number(contract.ltp))}. Taxes, fees
                        and fill price may differ.
                    </p>
                )}
                {!brokerStatus?.live_orders_enabled && (
                    <Alert
                        type="info"
                        message="Live orders are disabled by the server. This order cannot be submitted."
                    />
                )}
                {(!brokerStatus?.is_connected || !brokerStatus?.is_token_valid) && (
                    <Alert
                        type="warning"
                        message="Connect and validate your Zerodha session before submitting."
                    />
                )}
                {!marketIsLive && (
                    <Alert
                        type="warning"
                        message="Live order submission is unavailable while the market is closed."
                    />
                )}
                {marketIsLive && (!quoteFeedIsFresh || !chainIsFresh) && (
                    <Alert
                        type="warning"
                        message="The NIFTY quote or selected option quote is stale. Refresh and review current prices before submitting."
                    />
                )}
                {qty > 0 && qty % lotSize !== 0 && (
                    <p className="text-xs text-amber-300">
                        Quantity must be a multiple of the contract lot size ({lotSize}).
                    </p>
                )}
                <label className="flex items-start gap-2 text-xs leading-5 text-dark-300">
                    <input
                        type="checkbox"
                        className="mt-1 accent-fuchsia-400"
                        checked={acknowledged}
                        onChange={(event) => setAcknowledged(event.target.checked)}
                    />
                    I have reviewed this live order and want Athena to submit it to Zerodha.
                </label>
                <div className="flex justify-end gap-2">
                    <Button variant="secondary" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button
                        variant="danger"
                        loading={placing}
                        disabled={!canPlace || placing}
                        onClick={() =>
                            onPlace({
                                confirm_live_order: true,
                                tradingsymbol: contract.trading_symbol,
                                exchange: "NFO",
                                transaction_type: "BUY",
                                quantity: qty,
                                order_type: orderType,
                                product: "NRML",
                                price: orderType === "LIMIT" ? orderPrice : 0,
                            })
                        }
                    >
                        Place live order
                    </Button>
                </div>
            </div>
        </Modal>
    );
}

export default function DashboardMarketPanels({
    brokerStatus,
    aiSignals = [],
    quote,
    marketIsLive,
    quoteFeedIsFresh,
}) {
    const client = useQueryClient();
    const [expiry, setExpiry] = useState("");
    const [reviewOpen, setReviewOpen] = useState(false);
    const [orderMessage, setOrderMessage] = useState("");
    const [freshnessClock, setFreshnessClock] = useState(Date.now());
    useEffect(() => {
        const timer = window.setInterval(() => setFreshnessClock(Date.now()), 5000);
        return () => window.clearInterval(timer);
    }, []);
    const expiryQuery = useQuery({
        queryKey: ["dashboard-option-expiry", "NIFTY"],
        queryFn: () => marketAPI.getExpiry("NIFTY"),
        select: (res) => res.data.data || [],
        staleTime: 60_000,
    });
    useEffect(() => {
        if (!expiry && expiryQuery.data?.length) setExpiry(nearestExpiry(expiryQuery.data));
    }, [expiry, expiryQuery.data]);
    const params = expiry ? { expiry } : undefined;
    const chainQuery = useQuery({
        queryKey: ["dashboard-option-chain", "NIFTY", expiry],
        queryFn: () => marketAPI.getOptionChain("NIFTY", params),
        enabled: Boolean(expiry),
        select: (res) => res.data.data || [],
        refetchInterval: marketIsLive ? 15_000 : false,
    });
    const summaryQuery = useQuery({
        queryKey: ["dashboard-option-summary", "NIFTY", expiry],
        queryFn: () => marketAPI.getOptionChainSummary("NIFTY", params),
        enabled: Boolean(expiry),
        select: (res) => res.data.data || null,
        refetchInterval: marketIsLive ? 30_000 : false,
    });
    const readQuery = useQuery({
        queryKey: ["market-read", "NIFTY"],
        queryFn: () => marketAPI.getMarketRead("NIFTY"),
        select: (res) => res.data.data || null,
        staleTime: 30_000,
        refetchInterval: 30_000,
    });
    const positionsQuery = useQuery({
        queryKey: ["zerodha-positions"],
        queryFn: () => zerodhaAPI.getPositions(),
        enabled: Boolean(brokerStatus?.is_connected && brokerStatus?.is_token_valid),
        refetchInterval: 15_000,
        select: (res) => res.data.data?.net || [],
    });
    const orderMutation = useMutation({
        mutationFn: (payload) => zerodhaAPI.placeOrder(payload),
        onSuccess: (res) => {
            const data = res.data.data;
            setOrderMessage(
                data?.order_id
                    ? `Zerodha accepted the order request · ID ${data.order_id}. Check Live Orders for its current status.`
                    : "Zerodha did not return an order ID. Check Live Orders before retrying to avoid a duplicate."
            );
            setReviewOpen(false);
            client.invalidateQueries({ queryKey: ["zerodha-orders"] });
            client.invalidateQueries({ queryKey: ["zerodha-positions"] });
        },
        onError: (error) =>
            setOrderMessage(
                error?.response?.data?.message ||
                    "Order was not accepted. Check Zerodha status and try again."
            ),
    });
    const summary = summaryQuery.data;
    const chain = chainQuery.data || [];
    const atmRows = useMemo(() => {
        if (!summary?.atm_strike) return [];
        return chain.filter((row) => Number(row.strike) === Number(summary.atm_strike));
    }, [chain, summary?.atm_strike]);
    const atmCall = atmRows.find((row) => row.option_type === "CE");
    const atmPut = atmRows.find((row) => row.option_type === "PE");
    const ai = aiSignals.find(
        (signal) => signal.symbol === "NIFTY" && ["BUY", "SELL"].includes(signal.signal)
    );
    const aiContract = ai?.suggested_contract;
    useEffect(() => {
        if (aiContract?.expiry && aiContract.expiry !== expiry) setExpiry(aiContract.expiry);
    }, [ai?.id, aiContract?.expiry, expiry]);
    const contract = aiContract?.trading_symbol
        ? chain.find((row) => row.trading_symbol === aiContract.trading_symbol)
        : null;
    const snap = readQuery.data || {};
    const levels = snap.levels || {};
    const supportLevel = levels.support?.value == null ? null : levels.support;
    const resistanceLevel = levels.resistance?.value == null ? null : levels.resistance;
    const indicators = snap.indicators || {};
    const positions = positionsQuery.data || [];
    const openPositions = positions.filter((position) => Number(position.quantity) !== 0);
    const netPnl = openPositions.reduce(
        (total, position) => total + (Number(position.pnl) || 0),
        0
    );
    const contractQuoteTime = contract?.quote_timestamp
        ? new Date(contract.quote_timestamp).getTime()
        : Number.NaN;
    const contractQuoteAge = freshnessClock - contractQuoteTime;
    const chainIsFresh = Boolean(
        chainQuery.dataUpdatedAt &&
        freshnessClock - chainQuery.dataUpdatedAt <= 30_000 &&
        Number.isFinite(contractQuoteTime) &&
        contractQuoteAge >= 0 &&
        contractQuoteAge <= 60_000
    );
    const aiSignalTime = ai?.signal_time ? new Date(ai.signal_time).getTime() : Number.NaN;
    const aiSignalAgeMs = freshnessClock - aiSignalTime;
    const aiSignalIsFresh =
        Number.isFinite(aiSignalTime) && aiSignalAgeMs >= 0 && aiSignalAgeMs <= 15 * 60_000;
    const underlyingQuoteTime = quote?.timestamp ? new Date(quote.timestamp).getTime() : Number.NaN;
    const underlyingQuoteAge = freshnessClock - underlyingQuoteTime;
    const underlyingQuoteIsFresh = Boolean(
        Number.isFinite(underlyingQuoteTime) &&
        underlyingQuoteAge >= 0 &&
        underlyingQuoteAge <= 60_000
    );
    const orderCanOpen = Boolean(
        marketIsLive &&
        quoteFeedIsFresh &&
        underlyingQuoteIsFresh &&
        chainIsFresh &&
        aiSignalIsFresh &&
        brokerStatus?.live_orders_enabled &&
        brokerStatus?.is_connected &&
        brokerStatus?.is_token_valid &&
        contract?.trading_symbol
    );
    const spot = Number(quote?.ltp ?? summary?.spot_price);
    const vwap = indicators.vwap == null ? Number.NaN : Number(indicators.vwap);
    const ema = indicators.ema_20 == null ? Number.NaN : Number(indicators.ema_20);
    const pcr = summary?.pcr_oi;
    const finalDirection = ai?.signal
        ? `${ai.signal} · ${ai.confidence_score ?? 0}%`
        : "No current AI signal";

    return (
        <div className="space-y-4">
            <Card
                title="Market Read · NIFTY 50"
                subtitle="Observed market data and historical context · read-only."
                actions={
                    <span className="text-xs text-dark-500">
                        Last trade{" "}
                        {quote?.timestamp || snap.quote?.timestamp
                            ? formatDateTime(quote?.timestamp || snap.quote?.timestamp)
                            : "time unavailable"}
                    </span>
                }
            >
                {!marketIsLive && (
                    <Alert
                        type="info"
                        message="The market session is closed. Quote, option premium, and range figures show the last available session; request time does not mean the prices are live."
                    />
                )}
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                    <DataValue
                        label="LTP"
                        value={quote?.ltp == null ? "—" : `₹${fmt(quote.ltp)}`}
                        detail={
                            quote?.timestamp
                                ? `Last trade ${formatDateTime(quote.timestamp)} · ${quote.change_percent == null ? "change unavailable" : `${Number(quote.change_percent) >= 0 ? "+" : ""}${fmt(quote.change_percent)}% vs previous close`}`
                                : "Trade timestamp unavailable; verify freshness before relying on this quote."
                        }
                    />
                    <DataValue
                        label="Live position P&L"
                        value={
                            positionsQuery.isLoading
                                ? "Loading…"
                                : positionsQuery.isError
                                  ? "Unavailable"
                                  : formatCurrency(netPnl)
                        }
                        detail={`${openPositions.length} open Zerodha position${openPositions.length === 1 ? "" : "s"}`}
                    />
                    <DataValue
                        label="Historical direction baseline"
                        value={
                            snap.probability?.available
                                ? `↑ ${snap.probability.up_pct}% · ↓ ${snap.probability.down_pct}% · flat ${snap.probability.flat_pct}%`
                                : "Unavailable"
                        }
                        detail={
                            snap.probability?.basis ||
                            snap.probability?.reason ||
                            "No verified matched-session baseline."
                        }
                    />
                    <DataValue
                        label={
                            marketIsLive
                                ? "Expected range · intraday guide"
                                : "Last-session range guide"
                        }
                        value={
                            snap.range_guide
                                ? `${fmt(snap.range_guide.low, 0)} – ${fmt(snap.range_guide.high, 0)}`
                                : "Unavailable"
                        }
                        detail={
                            snap.range_guide
                                ? `${marketIsLive ? "Today’s" : "Last quote session’s"} open ${fmt(snap.range_guide.open, 0)} · ${snap.range_guide.sample_size ?? "—"} historical sessions${!marketIsLive && quote?.timestamp ? ` · quote ${formatDateTime(quote.timestamp)}` : ""}`
                                : snap.range_history?.unavailable_reason ||
                                  "Verified history is insufficient."
                        }
                    />
                </div>
                <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                    <DataValue
                        label="ATM strike · expiry"
                        value={
                            summary?.atm_strike
                                ? `${fmt(summary.atm_strike, 0)} · ${expiry || "—"}`
                                : "Unavailable"
                        }
                        detail={
                            summary?.spot_price
                                ? `Spot ${fmt(summary.spot_price)}`
                                : "Option-chain snapshot unavailable"
                        }
                    />
                    <DataValue
                        label="ATM call premium"
                        value={atmCall?.ltp == null ? "Unavailable" : `₹${fmt(atmCall.ltp)}`}
                        detail={
                            atmCall?.quote_timestamp
                                ? `NFO quote · ${formatDateTime(atmCall.quote_timestamp)}`
                                : "NFO quote timestamp unavailable"
                        }
                    />
                    <DataValue
                        label="ATM put premium"
                        value={atmPut?.ltp == null ? "Unavailable" : `₹${fmt(atmPut.ltp)}`}
                        detail={
                            atmPut?.quote_timestamp
                                ? `NFO quote · ${formatDateTime(atmPut.quote_timestamp)}`
                                : "NFO quote timestamp unavailable"
                        }
                    />
                    <DataValue
                        label="Combined ATM premium"
                        value={
                            atmRows.length === 2
                                ? `₹${fmt(atmRows.reduce((sum, row) => sum + Number(row.ltp || 0), 0))}`
                                : "Unavailable"
                        }
                        detail="Call + put LTP · not a profit estimate"
                    />
                    <DataValue
                        label="Support / resistance"
                        value={
                            !supportLevel && !resistanceLevel
                                ? "Unavailable"
                                : `${fmt(supportLevel?.value)} / ${fmt(resistanceLevel?.value)}`
                        }
                        detail={
                            supportLevel || resistanceLevel
                                ? `${supportLevel?.name || "No support below spot"} / ${resistanceLevel?.name || "No resistance above spot"} · stored candles through ${snap.source?.last_candle_at ? formatDateTime(snap.source.last_candle_at) : "unknown"}`
                                : levels.unavailable_reason ||
                                  "No verified pivot or CPR level is available around the current spot."
                        }
                    />
                </div>
                <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-dark-700 bg-dark-900/50 p-3">
                    <div>
                        <p className="text-sm font-semibold text-dark-100">
                            AI-selected NIFTY contract
                        </p>
                        <p className="mt-1 text-xs text-dark-400">
                            {aiContract
                                ? `${ai.signal} · ${ai.confidence_score}% confidence · ${aiContract.trading_symbol} · ${aiContract.expiry}`
                                : "Run a directional AI analysis with a verified contract before reviewing an order."}{" "}
                            Every order needs your separate review and confirmation.
                        </p>
                    </div>
                    <div className="flex flex-wrap items-end gap-2">
                        <Button
                            variant="danger"
                            disabled={!orderCanOpen || !contract || orderMutation.isPending}
                            onClick={() => {
                                setOrderMessage("");
                                setReviewOpen(true);
                            }}
                        >
                            Review AI order
                        </Button>
                    </div>
                </div>
                {!brokerStatus?.live_orders_enabled && (
                    <p className="mt-2 text-xs text-dark-500">
                        Live order submission is disabled by the server. The button stays
                        unavailable until the server permits it.
                    </p>
                )}
                {brokerStatus?.live_orders_enabled && !marketIsLive && (
                    <p className="mt-2 text-xs text-dark-500">
                        Live-order review is available only while the market is open.
                    </p>
                )}
                {marketIsLive &&
                    (!quoteFeedIsFresh || !underlyingQuoteIsFresh || !chainIsFresh) && (
                        <p className="mt-2 text-xs text-amber-300">
                            Order review is disabled until the NIFTY quote and selected option
                            contract both have trade timestamps from the last 60 seconds.
                        </p>
                    )}
                {ai && !aiSignalIsFresh && (
                    <p className="mt-2 text-xs text-amber-300">
                        The latest directional AI signal is older than 15 minutes. Run a fresh
                        analysis before reviewing an order.
                    </p>
                )}
                {(!ai || !aiContract) && (
                    <p className="mt-2 text-xs text-amber-300">
                        A current directional AI signal with a verified option contract is required
                        before an order can be prepared.
                    </p>
                )}
                {aiContract && !contract && !chainQuery.isLoading && (
                    <p className="mt-2 text-xs text-amber-300">
                        The AI-selected contract is not present in the current option-chain
                        response; refresh the chain before reviewing an order.
                    </p>
                )}
                {orderMessage && (
                    <p
                        role="status"
                        className="mt-2 rounded-lg border border-dark-700 bg-dark-900 p-3 text-sm text-dark-200"
                    >
                        {orderMessage}
                    </p>
                )}
            </Card>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(300px,0.8fr)]">
                <Card
                    title="Signal Breakdown"
                    subtitle="Current evidence only · values are not combined into a score."
                >
                    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                        <EvidenceChip
                            label="OI bias"
                            value={pcr == null ? null : `PCR ${fmt(pcr)}`}
                            note="Current put/call OI ratio; no historical change."
                        />
                        <EvidenceChip
                            label="ATM OI"
                            value={
                                atmRows.length
                                    ? `CE ${fmt(atmRows.find((row) => row.option_type === "CE")?.oi, 0)} · PE ${fmt(atmRows.find((row) => row.option_type === "PE")?.oi, 0)}`
                                    : null
                            }
                            note="Current chain snapshot."
                        />
                        <EvidenceChip
                            label="VWAP bias"
                            value={
                                Number.isFinite(vwap) && Number.isFinite(spot)
                                    ? `${spot >= vwap ? "Above" : "Below"} VWAP`
                                    : null
                            }
                            note={
                                indicators.vwap_unavailable_reason ||
                                (Number.isFinite(vwap)
                                    ? `VWAP ${fmt(vwap)}`
                                    : "Verified volume-weighted value unavailable.")
                            }
                        />
                        <EvidenceChip
                            label="Opening range"
                            value={null}
                            note="Opening-range levels are not present in the current dashboard snapshot."
                        />
                        <EvidenceChip
                            label="Technical"
                            value={
                                Number.isFinite(ema) && Number.isFinite(spot)
                                    ? `${spot >= ema ? "Above" : "Below"} EMA 20`
                                    : null
                            }
                            note={
                                indicators.ema_20_unavailable_reason ||
                                (Number.isFinite(ema)
                                    ? `RSI 14 ${fmt(indicators.rsi_14)} · EMA ${fmt(ema)}`
                                    : "Verified indicator values unavailable.")
                            }
                        />
                        <EvidenceChip
                            label="AI sentiment"
                            value={ai ? `${ai.signal} · ${ai.confidence_score}%` : null}
                            note={
                                ai
                                    ? `${ai.symbol} · ${formatDateTime(ai.signal_time)}`
                                    : "No saved AI signal is available."
                            }
                        />
                        <EvidenceChip
                            label="Momentum"
                            value={
                                quote?.change_percent == null
                                    ? null
                                    : `${Number(quote.change_percent) >= 0 ? "+" : ""}${fmt(quote.change_percent)}% today`
                            }
                            note="Underlying quote change; not an independent forecast."
                        />
                        <EvidenceChip
                            label="Opening gap"
                            value={
                                snap.quote?.gap_pct == null
                                    ? null
                                    : `${Number(snap.quote.gap_pct) >= 0 ? "+" : ""}${fmt(snap.quote.gap_pct)}%`
                            }
                            note="Open versus previous close."
                        />
                    </div>
                    <div className="mt-3 flex items-center justify-between border-t border-dark-700 pt-3">
                        <span className="text-sm text-dark-400">Final AI direction</span>
                        <Badge
                            variant={
                                ai?.signal === "BUY"
                                    ? "green"
                                    : ai?.signal === "SELL"
                                      ? "red"
                                      : "gray"
                            }
                        >
                            {finalDirection}
                        </Badge>
                    </div>
                    <p className="mt-2 text-xs text-dark-500">
                        Sources: {snap.source?.quote || "quote unavailable"}; option chain{" "}
                        {chainQuery.dataUpdatedAt
                            ? formatDateTime(chainQuery.dataUpdatedAt)
                            : "unavailable"}
                        ; indicators {snap.source?.indicators || "unavailable"}.
                    </p>
                </Card>
                <Card
                    title="Open Zerodha Positions"
                    subtitle="Live broker positions · refreshes every 15 seconds"
                    actions={
                        <a
                            className="text-xs text-primary-400 hover:text-primary-300"
                            href="/zerodha/positions"
                        >
                            View all
                        </a>
                    }
                >
                    {positionsQuery.isLoading ? (
                        <Spinner text="Loading positions…" />
                    ) : positionsQuery.isError ? (
                        <p className="text-sm text-dark-400">
                            Could not load positions. Check the Zerodha connection.
                        </p>
                    ) : openPositions.length === 0 ? (
                        <div className="flex items-center gap-3 rounded-lg border border-dark-700 bg-dark-900/40 p-4">
                            <BriefcaseBusiness className="h-5 w-5 text-dark-400" />
                            <p className="text-sm text-dark-300">No open positions.</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {openPositions.slice(0, 6).map((position) => (
                                <div
                                    key={`${position.tradingsymbol}-${position.product}`}
                                    className="flex items-center justify-between gap-3 rounded-lg border border-dark-700 bg-dark-900/40 p-3"
                                >
                                    <div>
                                        <p className="font-mono text-sm font-semibold text-dark-100">
                                            {position.tradingsymbol}
                                        </p>
                                        <p className="mt-1 text-xs text-dark-500">
                                            Qty {position.quantity} · Avg ₹
                                            {fmt(position.average_price)} · LTP ₹
                                            {fmt(position.last_price)}
                                        </p>
                                    </div>
                                    <p
                                        className={`font-mono text-sm font-semibold ${Number(position.pnl) >= 0 ? "text-green-400" : "text-red-400"}`}
                                    >
                                        {formatCurrency(position.pnl)}
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}
                    <div className="mt-3 flex items-center gap-2 text-xs text-dark-500">
                        {brokerStatus?.is_connected ? (
                            <ShieldCheck className="h-3.5 w-3.5 text-green-400" />
                        ) : (
                            <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
                        )}
                        {brokerStatus?.is_connected
                            ? "Zerodha session connected"
                            : "Zerodha session not connected"}
                    </div>
                </Card>
            </div>
            {readQuery.isError && (
                <p className="flex items-center gap-2 text-xs text-amber-300">
                    <TriangleAlert className="h-4 w-4" />
                    Market Read could not load; the cards above retain unavailable explanations.
                </p>
            )}
            <LiveOrderReview
                open={reviewOpen}
                onClose={() => setReviewOpen(false)}
                contract={contract}
                brokerStatus={brokerStatus}
                marketIsLive={marketIsLive}
                quoteFeedIsFresh={Boolean(quoteFeedIsFresh && underlyingQuoteIsFresh)}
                chainIsFresh={chainIsFresh}
                placing={orderMutation.isPending}
                onPlace={(payload) => orderMutation.mutate(payload)}
            />
        </div>
    );
}
