import { Activity, Clock3, Info } from "lucide-react";
import { Badge, Card } from "../../../components/common";
import { formatDateTime, formatNumber } from "../../../utils/formatters";

function validNumber(value) {
    return value !== null && value !== undefined && Number.isFinite(Number(value));
}

function price(value) {
    return validNumber(value) ? `₹${formatNumber(value, 2)}` : "—";
}

function Evidence({ label, status, value, detail, tone = "neutral" }) {
    const colors = {
        positive: "border-green-500/30 bg-green-500/5 text-green-300",
        negative: "border-red-500/30 bg-red-500/5 text-red-300",
        neutral: "border-dark-700 bg-dark-900 text-dark-200",
        unavailable: "border-dark-700 bg-dark-900 text-dark-500",
    };

    return (
        <div className={`min-w-0 rounded-lg border px-3 py-2.5 ${colors[tone] || colors.neutral}`}>
            <div className="flex items-center justify-between gap-2">
                <p className="truncate text-xs font-semibold">{label}</p>
                <span className="shrink-0 text-[10px] font-bold uppercase tracking-wide opacity-80">
                    {status}
                </span>
            </div>
            <p className="mt-1 truncate font-mono text-sm font-semibold">{value}</p>
            <p className="mt-1 text-[11px] leading-4 text-dark-400">{detail}</p>
        </div>
    );
}

function ProbabilityCard({ probability }) {
    if (!probability?.available) {
        return (
            <Card
                title="Historical move outcomes"
                subtitle="Matched by today's opening-gap category"
            >
                <p className="text-sm text-dark-400">
                    {probability?.reason ||
                        "Unavailable — waiting for a valid quote and sufficient historical data."}
                </p>
                <p className="mt-3 text-xs text-dark-500">
                    No directional probability is inferred when a matching sample is unavailable.
                </p>
            </Card>
        );
    }

    const outcomes = [
        {
            label: "Closed up",
            value: probability.up_pct,
            color: "bg-green-500",
            text: "text-green-300",
        },
        {
            label: "Closed down",
            value: probability.down_pct,
            color: "bg-red-500",
            text: "text-red-300",
        },
        { label: "Flat", value: probability.flat_pct, color: "bg-dark-500", text: "text-dark-200" },
    ];

    return (
        <Card
            title="Historical move outcomes"
            subtitle="Full-session close vs. open · same opening-gap category"
        >
            <div
                className="flex h-2.5 overflow-hidden rounded-full bg-dark-800"
                aria-label="Historical outcome distribution"
            >
                {outcomes.map((item) => (
                    <span
                        key={item.label}
                        className={item.color}
                        style={{ width: `${Math.max(0, Math.min(100, Number(item.value) || 0))}%` }}
                    />
                ))}
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2">
                {outcomes.map((item) => (
                    <div key={item.label}>
                        <p className={`font-mono text-lg font-bold ${item.text}`}>
                            {validNumber(item.value) ? `${formatNumber(item.value, 1)}%` : "—"}
                        </p>
                        <p className="text-[11px] text-dark-400">{item.label}</p>
                    </div>
                ))}
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-dark-400">
                <Badge variant={probability.low_confidence ? "yellow" : "gray"}>
                    {probability.low_confidence ? "Small sample" : "Historical sample"}
                </Badge>
                <span>
                    n = {probability.sample_size} · {probability.gap_bucket?.replaceAll("_", " ")}
                </span>
            </div>
            <p className="mt-2 text-[11px] leading-4 text-dark-500">
                {probability.basis} Data through{" "}
                {probability.historical_through
                    ? formatDateTime(probability.historical_through)
                    : "an unknown date"}
                . This describes past sessions; it is not a forecast or odds for the remaining
                session.
            </p>
        </Card>
    );
}

function RangeCard({ rangeGuide, rangeHistory }) {
    if (!rangeGuide) {
        return (
            <Card
                title="Expected-range reference"
                subtitle="Historical median day excursions from today's open"
            >
                <p className="text-sm text-dark-400">
                    Unavailable —{" "}
                    {rangeHistory?.unavailable_reason ||
                        "a valid session open and sufficient stored daily history are required."}
                </p>
                {validNumber(rangeHistory?.sample_size) && (
                    <p className="mt-2 text-xs text-dark-500">
                        Available daily sessions: {rangeHistory.sample_size}.
                    </p>
                )}
            </Card>
        );
    }

    return (
        <Card
            title="Expected-range reference"
            subtitle="Historical median day excursions from today's open"
        >
            <div className="flex items-baseline justify-between gap-3">
                <p className="font-mono text-xl font-bold text-dark-50">
                    {formatNumber(rangeGuide.low, 0)} – {formatNumber(rangeGuide.high, 0)}
                </p>
                <Badge variant={rangeGuide.low_confidence ? "yellow" : "gray"}>
                    {rangeGuide.low_confidence ? "Limited sample" : "Historical guide"}
                </Badge>
            </div>
            <p className="mt-2 text-xs text-dark-400">
                Open {formatNumber(rangeGuide.open, 2)} · median +
                {formatNumber(rangeGuide.median_up_points, 1)} / −
                {formatNumber(rangeGuide.median_down_points, 1)} points
            </p>
            <p className="mt-2 text-[11px] leading-4 text-dark-500">
                Based on {rangeGuide.sample_size ?? rangeHistory?.sample_size ?? "—"} stored daily
                sessions through{" "}
                {rangeGuide.historical_through
                    ? formatDateTime(rangeGuide.historical_through)
                    : "an unknown date"}
                . Descriptive reference, not a forecast, confidence interval, or remaining-session
                range.
            </p>
        </Card>
    );
}

function AtmPremiumCard({ summary, chain, expiry, fetchedAt }) {
    const strike = Number(summary?.atm_strike);
    const call = chain.find(
        (row) =>
            Number(row.strike) === strike &&
            ["CE", "CALL"].includes(String(row.option_type).toUpperCase())
    );
    const put = chain.find(
        (row) =>
            Number(row.strike) === strike &&
            ["PE", "PUT"].includes(String(row.option_type).toUpperCase())
    );
    const callPremium = validNumber(call?.ltp) && Number(call.ltp) > 0 ? Number(call.ltp) : null;
    const putPremium = validNumber(put?.ltp) && Number(put.ltp) > 0 ? Number(put.ltp) : null;
    const straddle = callPremium !== null && putPremium !== null ? callPremium + putPremium : null;
    const lower = straddle !== null ? Math.max(0, strike - straddle) : null;
    const upper = straddle !== null ? strike + straddle : null;
    const callUnavailable =
        callPremium === null
            ? call
                ? "The broker returned no usable premium for the ATM call."
                : "No ATM call quote was returned for this expiry."
            : null;
    const putUnavailable =
        putPremium === null
            ? put
                ? "The broker returned no usable premium for the ATM put."
                : "No ATM put quote was returned for this expiry."
            : null;

    return (
        <Card
            title="ATM premium snapshot"
            subtitle={`${expiry || "Selected expiry"}${validNumber(strike) ? ` · ${formatNumber(strike, 0)} strike` : " · ATM strike unavailable"}`}
        >
            <div className="grid grid-cols-2 gap-3">
                <div>
                    <p className="text-xs text-dark-400">Call premium</p>
                    <p className="mt-1 font-mono text-lg font-semibold text-green-300">
                        {price(callPremium)}
                    </p>
                    {callUnavailable && (
                        <p className="mt-1 text-[11px] leading-4 text-dark-500">
                            {callUnavailable}
                        </p>
                    )}
                </div>
                <div>
                    <p className="text-xs text-dark-400">Put premium</p>
                    <p className="mt-1 font-mono text-lg font-semibold text-red-300">
                        {price(putPremium)}
                    </p>
                    {putUnavailable && (
                        <p className="mt-1 text-[11px] leading-4 text-dark-500">{putUnavailable}</p>
                    )}
                </div>
            </div>
            <div className="mt-3 rounded-lg border border-dark-700 bg-dark-900 px-3 py-2">
                <div className="flex justify-between gap-3 text-xs">
                    <span className="text-dark-400">Combined ATM straddle</span>
                    <span className="font-mono font-semibold text-dark-100">{price(straddle)}</span>
                </div>
                <div className="mt-1 flex justify-between gap-3 text-xs">
                    <span className="text-dark-400">Theoretical expiry break-even</span>
                    <span className="font-mono text-dark-200">
                        {lower !== null
                            ? `${formatNumber(lower, 0)} – ${formatNumber(upper, 0)}`
                            : "—"}
                    </span>
                </div>
            </div>
            <p className="mt-2 text-[11px] leading-4 text-dark-500">
                Uses quoted ATM call + put premiums. Break-even is for a long straddle at expiry
                before fees/slippage; it is not a target or a recommendation.
            </p>
            <p className="mt-2 inline-flex items-center gap-1 text-[11px] text-dark-500">
                <Clock3 className="h-3 w-3" /> Chain response fetched{" "}
                {fetchedAt ? formatDateTime(fetchedAt) : "—"}; exchange quote time is not supplied.
            </p>
        </Card>
    );
}

function LevelsCard({ levels, spot, lastCandleAt, isIntradayStale }) {
    const rows = [
        { label: "Nearest support", level: levels?.support },
        { label: "Nearest resistance", level: levels?.resistance },
    ];

    return (
        <Card
            title="Support & resistance"
            subtitle="Nearest levels from the latest stored 15-minute candle inputs"
        >
            {levels?.available ? (
                <div className="space-y-3">
                    {rows.map(({ label, level }) => (
                        <div key={label} className="flex items-center justify-between gap-3">
                            <span className="text-sm text-dark-400">{label}</span>
                            <span className="text-right">
                                <span className="font-mono text-sm font-semibold text-dark-100">
                                    {level ? formatNumber(level.value, 2) : "—"}
                                </span>
                                {level && validNumber(spot) && (
                                    <span className="ml-2 text-xs text-dark-500">
                                        {formatNumber(Math.abs(Number(spot) - level.value), 1)} pts
                                        · {level.method} {level.name}
                                    </span>
                                )}
                            </span>
                        </div>
                    ))}
                    <p className="border-t border-dark-800 pt-2 text-[11px] leading-4 text-dark-500">
                        Levels use pivot and CPR values from stored 15-minute candles; last input
                        candle {lastCandleAt ? formatDateTime(lastCandleAt) : "time unavailable"}.{" "}
                        {!validNumber(spot) ? (
                            "A current spot quote is needed to classify nearby support and resistance."
                        ) : (
                            <>
                                {!levels?.support &&
                                    "No calculated level is below the current spot. "}
                                {!levels?.resistance &&
                                    "No calculated level is above the current spot."}
                            </>
                        )}
                    </p>
                </div>
            ) : (
                <p className="text-sm text-dark-400">
                    {isIntradayStale
                        ? `Withheld: the latest 15-minute candle is stale (${lastCandleAt ? formatDateTime(lastCandleAt) : "timestamp unavailable"}).`
                        : levels?.unavailable_reason ||
                          "Unavailable — no usable stored 15-minute pivot inputs."}
                </p>
            )}
        </Card>
    );
}

function EvidenceCard({ snapshot, summary }) {
    const spot = Number(snapshot?.quote?.spot ?? summary?.spot_price);
    const indicators = snapshot?.indicators ?? {};
    const vwap = Number(indicators.vwap);
    const ema = Number(indicators.ema_20);
    const rsi = Number(indicators.rsi_14);
    const pcr = Number(summary?.pcr_oi);
    const gap = snapshot?.probability;

    const vwapValid = Number.isFinite(spot) && Number.isFinite(vwap) && vwap > 0;
    const emaValid = Number.isFinite(spot) && Number.isFinite(ema) && ema > 0;
    const rsiValid = validNumber(indicators.rsi_14);
    const vwapTone = !vwapValid
        ? "unavailable"
        : spot > vwap
          ? "positive"
          : spot < vwap
            ? "negative"
            : "neutral";
    const emaTone = !emaValid
        ? "unavailable"
        : spot > ema
          ? "positive"
          : spot < ema
            ? "negative"
            : "neutral";
    const rsiTone = !rsiValid
        ? "unavailable"
        : rsi >= 55
          ? "positive"
          : rsi <= 45
            ? "negative"
            : "neutral";
    const rsiStatus = !rsiValid
        ? "Unavailable"
        : rsi >= 55
          ? "Positive"
          : rsi <= 45
            ? "Negative"
            : "Neutral";

    return (
        <Card
            title="Signal evidence"
            subtitle="Independent observations · statuses are not a combined trade signal"
        >
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                <Evidence
                    label="Price vs VWAP"
                    status={
                        !vwapValid
                            ? "Unavailable"
                            : spot > vwap
                              ? "Above"
                              : spot < vwap
                                ? "Below"
                                : "At level"
                    }
                    value={vwapValid ? formatNumber(vwap, 2) : "—"}
                    detail={
                        vwapValid
                            ? `Session VWAP from ${indicators.vwap_candle_count} volume-bearing of ${indicators.vwap_session_candle_count} stored 15-minute bars.`
                            : indicators.vwap_unavailable_reason ||
                              "VWAP is unavailable because current-session volume data is missing."
                    }
                    tone={vwapTone}
                />
                <Evidence
                    label="Price vs EMA 20"
                    status={
                        !emaValid
                            ? "Unavailable"
                            : spot > ema
                              ? "Above"
                              : spot < ema
                                ? "Below"
                                : "At level"
                    }
                    value={emaValid ? formatNumber(ema, 2) : "—"}
                    detail={
                        !emaValid
                            ? indicators.ema_20_unavailable_reason ||
                              "EMA 20 could not be calculated from the available candle history."
                            : snapshot?.freshness?.intraday_is_stale
                              ? "Withheld because intraday candles are stale."
                              : "EMA 20 from stored 15-minute candles; not a standalone signal."
                    }
                    tone={emaTone}
                />
                <Evidence
                    label="RSI 14 momentum"
                    status={rsiStatus}
                    value={rsiValid ? formatNumber(rsi, 1) : "—"}
                    detail={
                        !rsiValid
                            ? indicators.rsi_14_unavailable_reason ||
                              "RSI 14 could not be calculated from the available candle history."
                            : snapshot?.freshness?.intraday_is_stale
                              ? "Withheld because intraday candles are stale."
                              : "Descriptive bands: above 55 positive, below 45 negative; otherwise neutral."
                    }
                    tone={rsiTone}
                />
                <Evidence
                    label="Opening-gap base rate"
                    status={gap?.available ? "Historical" : "Unavailable"}
                    value={
                        gap?.available
                            ? `${gap.gap_bucket?.replaceAll("_", " ")} · n=${gap.sample_size}`
                            : "—"
                    }
                    detail="Past full-session outcomes conditional on opening-gap category; not a forecast."
                    tone="neutral"
                />
                <Evidence
                    label="Put / call OI ratio"
                    status={validNumber(pcr) ? "Context only" : "Unavailable"}
                    value={validNumber(pcr) ? formatNumber(pcr, 2) : "—"}
                    detail="Expiry-chain PCR; PCR alone does not establish bullish or bearish OI bias."
                    tone="neutral"
                />
                <Evidence
                    label="ORB / news sentiment"
                    status="Unavailable"
                    value="Not assessed"
                    detail="No verified opening-range breakout or current news-sentiment input is available in this snapshot."
                    tone="unavailable"
                />
            </div>
            <details className="mt-3 rounded-lg border border-dark-800 px-3 py-2 text-xs text-dark-400">
                <summary className="flex cursor-pointer list-none items-center gap-2 font-semibold text-dark-300">
                    <Info className="h-3.5 w-3.5" />
                    Data sources and interpretation
                </summary>
                <ul className="mt-2 space-y-1.5 leading-5">
                    <li>
                        Quote: {snapshot?.source?.quote || "Configured market-data provider"};
                        fetched{" "}
                        {snapshot?.source?.quote_fetched_at
                            ? formatDateTime(snapshot.source.quote_fetched_at)
                            : "time unavailable"}
                        . This is the request time, not the exchange tick time.
                    </li>
                    <li>
                        Technical inputs:{" "}
                        {snapshot?.source?.indicators || "Stored 15-minute candles"}; latest candle{" "}
                        {snapshot?.source?.last_candle_at
                            ? formatDateTime(snapshot.source.last_candle_at)
                            : "not available"}
                        .
                    </li>
                    <li>
                        Empirical probability/range uses stored daily candles through{" "}
                        {snapshot?.source?.last_daily_candle_at
                            ? formatDateTime(snapshot.source.last_daily_candle_at)
                            : "an unknown date"}
                        ; sample size and horizon are shown with each statistic.
                    </li>
                    <li>
                        Green/red encode comparisons only. This panel has no aggregate score,
                        forecast, or order action.
                    </li>
                </ul>
            </details>
        </Card>
    );
}

export default function MarketReadPanel({
    symbol,
    expiry,
    summary,
    chain,
    chainFetchedAt,
    snapshot,
    isLoading,
    isError,
}) {
    const status = snapshot?.session?.session;

    return (
        <section className="space-y-3" aria-label="Read-only market read">
            <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                    <h2 className="text-lg font-semibold text-dark-100">Market Read</h2>
                    <p className="text-xs text-dark-400">
                        Evidence and historical context for {symbol}; no order actions.
                    </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-dark-400">
                    <Activity className="h-3.5 w-3.5" />
                    <span>
                        {status === "LIVE"
                            ? "Market open"
                            : status
                              ? status.replaceAll("_", " ").toLowerCase()
                              : "Session status unavailable"}
                    </span>
                    <span>·</span>
                    <span>
                        Snapshot{" "}
                        {snapshot?.as_of
                            ? formatDateTime(snapshot.as_of)
                            : isLoading
                              ? "loading"
                              : "unavailable"}
                    </span>
                </div>
            </div>
            {snapshot?.freshness?.intraday_is_stale && (
                <p
                    className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs leading-5 text-amber-200"
                    role="status"
                >
                    Intraday technicals are withheld: the latest stored 15-minute candle is{" "}
                    {snapshot.source?.last_candle_at
                        ? formatDateTime(snapshot.source.last_candle_at)
                        : "unavailable"}
                    . Quote and option-chain data may be newer.
                </p>
            )}
            {isError && (
                <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
                    Market-read history could not be loaded. ATM metrics below use the already
                    loaded option-chain data where available.
                </p>
            )}
            <div className="grid gap-3 xl:grid-cols-3">
                <ProbabilityCard probability={snapshot?.probability} />
                <RangeCard
                    rangeGuide={snapshot?.range_guide}
                    rangeHistory={snapshot?.range_history}
                />
                <AtmPremiumCard
                    summary={summary}
                    chain={chain}
                    expiry={expiry}
                    fetchedAt={chainFetchedAt}
                />
            </div>
            <div className="grid gap-3 xl:grid-cols-[minmax(280px,0.85fr)_minmax(0,1.5fr)]">
                <LevelsCard
                    levels={snapshot?.levels}
                    spot={snapshot?.quote?.spot ?? summary?.spot_price}
                    lastCandleAt={snapshot?.source?.last_candle_at}
                    isIntradayStale={snapshot?.freshness?.intraday_is_stale}
                />
                <EvidenceCard snapshot={snapshot} summary={summary} />
            </div>
        </section>
    );
}
