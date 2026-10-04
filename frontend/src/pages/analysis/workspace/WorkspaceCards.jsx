import { Link } from "react-router-dom";
import { Minus, TrendingDown, TrendingUp } from "lucide-react";
import { Badge, Card } from "../../../components/common";
import { isNumber, lakh, num, percent, signed, toLines, toNumber, whole } from "./format";

const TREND_VARIANT = { Bullish: "green", Bearish: "red", Neutral: "gray" };
const TREND_ICON = { Bullish: TrendingUp, Bearish: TrendingDown, Neutral: Minus };

function Stat({ label, value, hint, tone }) {
    const color = tone === "up" ? "text-green-400" : tone === "down" ? "text-red-400" : "";
    return (
        <div className="rounded-lg bg-dark-800/60 p-3" title={hint}>
            <p className="text-[11px] uppercase tracking-wide text-dark-500">{label}</p>
            <p className={`mt-1 text-sm font-semibold font-mono text-dark-100 ${color}`}>{value}</p>
        </div>
    );
}

function Na({ children }) {
    return <p className="text-sm text-dark-500">{children}</p>;
}

// ---------------------------------------------------------------- Verdict

export function VerdictPanel({ result, error, running, mode }) {
    if (running) {
        return (
            <Card title="Athena's read">
                <Na>Analysing verified data. This takes a few seconds…</Na>
            </Card>
        );
    }
    if (error) {
        return (
            <Card title="Athena's read">
                <p className="text-sm text-red-400">{error}</p>
            </Card>
        );
    }
    if (!result) {
        return (
            <Card title="Athena's read">
                <Na>
                    Press <strong className="text-dark-200">Run Analysis</strong> for a short, plain
                    read of the market. It explains its evidence and what it is unsure about. It
                    never places an order.
                </Na>
            </Card>
        );
    }

    const bias =
        result.signal === "BUY"
            ? "Bullish"
            : result.signal === "SELL"
              ? "Bearish"
              : "No clear edge";
    const variant = result.signal === "BUY" ? "green" : result.signal === "SELL" ? "red" : "gray";
    const supporting = toLines(result.supporting_evidence);
    const offsetting = toLines(result.conflicting_evidence);
    const missing = toLines(result.missing_information);

    return (
        <Card
            title="Athena's read"
            subtitle={
                mode === "NEXT_SESSION"
                    ? "Next-session planning outlook · not a trade signal"
                    : "Conditional analysis · educational, not advice"
            }
            actions={<Badge variant={variant}>{bias}</Badge>}
        >
            {result.confidence != null && (
                <p className="text-xs text-dark-400">
                    Evidence confidence {result.confidence}% · this is not a chance of profit.
                </p>
            )}
            {result.no_trade_reason && (
                <p className="mt-2 text-sm text-dark-200">{result.no_trade_reason}</p>
            )}
            <div className="mt-3 grid gap-4 md:grid-cols-2">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-dark-500">
                        Why
                    </p>
                    {supporting.length ? (
                        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-dark-200">
                            {supporting.slice(0, 5).map((line) => (
                                <li key={line}>{line}</li>
                            ))}
                        </ul>
                    ) : (
                        <Na>No supporting evidence was returned.</Na>
                    )}
                </div>
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-dark-500">
                        Offsetting
                    </p>
                    {offsetting.length ? (
                        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-dark-300">
                            {offsetting.slice(0, 5).map((line) => (
                                <li key={line}>{line}</li>
                            ))}
                        </ul>
                    ) : (
                        <Na>Nothing flagged.</Na>
                    )}
                </div>
            </div>
            {missing.length > 0 && (
                <p className="mt-3 text-xs text-amber-300">
                    Not available for this run: {missing.slice(0, 4).join("; ")}
                </p>
            )}
            <p className="mt-3 text-xs text-dark-500">
                <Link to="/analysis/history" className="underline">
                    Analysis history
                </Link>
            </p>
        </Card>
    );
}

// ------------------------------------------------------------ Price strip

export function PriceStrip({ symbol, report }) {
    const spot = report?.spot;
    const metrics = report?.key_metrics || {};
    const futures = metrics.futures;
    const vix = metrics.vix;
    const gap = metrics.gap;
    const breadth = metrics.breadth;
    const change = toNumber(spot?.change);
    const tone = change === null ? undefined : change >= 0 ? "up" : "down";

    return (
        <Card>
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <p className="text-xs uppercase tracking-wide text-dark-500">{symbol}</p>
                    <p className="font-mono text-3xl font-bold text-dark-50">{num(spot?.ltp)}</p>
                    <p
                        className={`font-mono text-sm ${tone === "up" ? "text-green-400" : tone === "down" ? "text-red-400" : "text-dark-400"}`}
                    >
                        {change === null
                            ? "NA"
                            : `${signed(spot?.change)} (${percent(spot?.change_percent)})`}
                    </p>
                </div>
                <Badge variant={report?.session?.is_live ? "green" : "gray"}>
                    {report?.session?.session ?? "NA"}
                </Badge>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-6">
                <Stat label="Day low" value={num(spot?.low)} />
                <Stat label="Open" value={num(spot?.open)} />
                <Stat label="Prev close" value={num(spot?.close)} />
                <Stat label="Day high" value={num(spot?.high)} />
                <Stat
                    label="Futures VWAP"
                    value={num(futures?.vwap)}
                    hint="Volume-weighted average price of the front-month future for the day."
                />
                <Stat label="Futures volume" value={futures ? whole(futures.volume) : "NA"} />
                <Stat
                    label="India VIX"
                    value={vix ? `${num(vix.ltp)} (${percent(vix.change_pct, 1)})` : "NA"}
                />
                <Stat
                    label="Futures OI"
                    value={futures ? lakh(futures.oi) : "NA"}
                    hint="Open interest: outstanding contracts, not buy or sell orders."
                />
                <Stat
                    label="Gap"
                    value={
                        gap
                            ? gap.direction === "FLAT"
                                ? "Flat open"
                                : `${gap.direction} ${signed(gap.gap_points, 0)} · ${gap.retrace_pct}% retraced`
                            : "NA"
                    }
                />
                <Stat
                    label="Breadth"
                    value={breadth ? `${breadth.advances} up / ${breadth.declines} down` : "NA"}
                    hint={
                        breadth
                            ? `${breadth.sample_size} of ${breadth.of_total} constituents quoted${breadth.low_confidence ? " (limited sample)" : ""}`
                            : "Constituent quotes were not available."
                    }
                />
            </div>
        </Card>
    );
}

// ------------------------------------------------------------ Trend check

function overallTrend(rows) {
    const trends = rows.map(([, row]) => row?.trend).filter(Boolean);
    if (!trends.length) return null;
    const bull = trends.filter((t) => t === "Bullish").length;
    const bear = trends.filter((t) => t === "Bearish").length;
    if (bull === trends.length) return "Bullish on every timeframe.";
    if (bear === trends.length) return "Bearish on every timeframe.";
    if (bull > bear) return "Leaning bullish, but the timeframes do not all agree.";
    if (bear > bull) return "Leaning bearish, but the timeframes do not all agree.";
    return "Mixed: the timeframes disagree.";
}

export function TrendCheck({ report }) {
    const labels = {
        "5m": "5 min · near term",
        "15m": "15 min · confirmation",
        "30m": "30 min · context",
    };
    const rows = Object.entries(report?.multi_timeframe || {});
    const summary = overallTrend(rows);

    return (
        <Card
            title="Intraday trend check"
            subtitle="Price against EMA 20 / EMA 50, with RSI 14, from stored candles"
        >
            {rows.length === 0 ? (
                <Na>No candle data is stored for this market yet.</Na>
            ) : (
                <div className="space-y-2">
                    {rows.map(([tf, row]) => {
                        const Icon = TREND_ICON[row?.trend] || Minus;
                        return (
                            <div
                                key={tf}
                                className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-dark-800/60 px-3 py-2"
                            >
                                <div>
                                    <p className="text-sm text-dark-100">{labels[tf] || tf}</p>
                                    <p className="font-mono text-xs text-dark-400">
                                        {row
                                            ? `EMA ${whole(row.ema_20)} / ${isNumber(row.ema_50) ? whole(row.ema_50) : "NA"} · RSI ${num(row.rsi_14, 1)}`
                                            : "Not enough candles"}
                                    </p>
                                </div>
                                <Badge variant={TREND_VARIANT[row?.trend] || "gray"}>
                                    <Icon className="mr-1 h-3 w-3" />
                                    {row?.trend || "NA"}
                                </Badge>
                            </div>
                        );
                    })}
                    {summary && <p className="pt-1 text-sm text-dark-300">Overall: {summary}</p>}
                </div>
            )}
        </Card>
    );
}

// ---------------------------------------------------------------- Levels

export function LevelsCard({ report }) {
    const sr = report?.support_resistance;
    const pivot = sr?.pivot || {};
    const cpr = sr?.cpr || {};
    const available = isNumber(pivot.pp);
    const source = sr?.based_on?.date;

    return (
        <Card
            title="Levels to watch"
            subtitle={
                available
                    ? `Classic pivots and CPR from the ${source} session high / low / close`
                    : "Pivots and CPR"
            }
        >
            {!available ? (
                <Na>
                    Unavailable: no completed daily candle is stored for this market, so pivot
                    levels cannot be calculated.
                </Na>
            ) : (
                <>
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                        <Stat label="R2" value={num(pivot.r2, 1)} />
                        <Stat label="R1" value={num(pivot.r1, 1)} />
                        <Stat label="Pivot (PP)" value={num(pivot.pp, 1)} />
                        <Stat label="S1" value={num(pivot.s1, 1)} />
                        <Stat label="S2" value={num(pivot.s2, 1)} />
                        <Stat label="CPR top" value={num(cpr.tc, 1)} />
                        <Stat label="CPR bottom" value={num(cpr.bc, 1)} />
                        <Stat label="CPR width" value={num(cpr.width, 1)} />
                    </div>
                    <p className="mt-2 text-xs text-dark-500">
                        Reference levels, not predictions. Price can pass through any of them.
                    </p>
                </>
            )}
        </Card>
    );
}

// --------------------------------------------------------------- Outlook

export function OutlookCard({ result }) {
    const probability = result?.probability;
    const sentiment = result?.sentiment;
    const hasProbability = probability && probability.upside_pct != null;
    const reasons = toLines(sentiment?.key_reasons);

    return (
        <Card
            title="Sentiment & probability"
            subtitle="Historical frequency for the chosen horizon, shown separately from direction"
        >
            {!result ? (
                <Na>Run the analysis to see this.</Na>
            ) : (
                <>
                    {sentiment?.classification && (
                        <p className="mb-3 text-sm text-dark-200">
                            Sentiment: <strong>{sentiment.classification}</strong>
                            {sentiment.confidence_pct != null &&
                                ` · confidence ${sentiment.confidence_pct}%`}
                        </p>
                    )}
                    {hasProbability ? (
                        <div className="grid grid-cols-3 gap-2 text-center">
                            <Stat label="Upward" value={`${probability.upside_pct}%`} tone="up" />
                            <Stat
                                label="Downward"
                                value={`${probability.downside_pct}%`}
                                tone="down"
                            />
                            <Stat label="Sideways" value={`${probability.sideways_pct}%`} />
                        </div>
                    ) : (
                        <Na>
                            {probability?.basis ||
                                "Unavailable: needs a verified, horizon-matched historical base rate."}
                        </Na>
                    )}
                    {hasProbability && (
                        <p className="mt-2 text-xs text-dark-500">
                            {probability.basis ||
                                `Observed frequency across ${probability.sample_size ?? "NA"} matched sessions.`}
                            {probability.low_confidence ? " Limited sample." : ""} Descriptive, not
                            a prediction.
                        </p>
                    )}
                    {reasons.length > 0 && (
                        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-dark-300">
                            {reasons.slice(0, 4).map((line) => (
                                <li key={line}>{line}</li>
                            ))}
                        </ul>
                    )}
                </>
            )}
        </Card>
    );
}

// ----------------------------------------------------------- Expectation

export function ExpectationCard({ result, spot }) {
    const expectation = result?.price_expectation;
    const low = toNumber(expectation?.expected_range_low);
    const high = toNumber(expectation?.expected_range_high);
    const price = toNumber(spot?.ltp);
    const hasRange = low !== null && high !== null && high > low;
    const position =
        hasRange && price !== null
            ? Math.min(100, Math.max(0, ((price - low) / (high - low)) * 100))
            : null;

    return (
        <Card title="Price expectation" subtitle="Typical historical excursion, not a forecast">
            {!result ? (
                <Na>Run the analysis to see this.</Na>
            ) : (
                <>
                    {hasRange ? (
                        <div className="mb-4">
                            <div className="relative h-2 rounded-full bg-dark-800">
                                {position !== null && (
                                    <div
                                        className="absolute top-1/2 h-4 w-1 -translate-y-1/2 rounded bg-primary-400"
                                        style={{ left: `${position}%` }}
                                        title={`Current price ${num(price)}`}
                                    />
                                )}
                            </div>
                            <div className="mt-1 flex justify-between font-mono text-xs text-dark-400">
                                <span>{num(low, 0)}</span>
                                <span>{num(high, 0)}</span>
                            </div>
                        </div>
                    ) : (
                        <Na>
                            Historical range unavailable: verified history or the session open is
                            missing.
                        </Na>
                    )}
                    <div className="grid grid-cols-2 gap-2">
                        <Stat
                            label="Nearest support"
                            value={num(expectation?.nearest_support, 1)}
                        />
                        <Stat
                            label="Nearest resistance"
                            value={num(expectation?.nearest_resistance, 1)}
                        />
                    </div>
                    {expectation?.basis && (
                        <p className="mt-2 text-xs text-dark-500">{expectation.basis}</p>
                    )}
                </>
            )}
        </Card>
    );
}

// ------------------------------------------------------- Option snapshot

function Leg({ title, leg }) {
    return (
        <div className="rounded-lg bg-dark-800/60 p-3">
            <p className="text-xs font-semibold text-dark-300">{title}</p>
            {leg ? (
                <div className="mt-1 space-y-0.5 font-mono text-sm text-dark-100">
                    <p>₹{num(leg.ltp)}</p>
                    <p className="text-xs text-dark-400">OI {whole(leg.oi)}</p>
                    <p className="text-xs text-dark-400">
                        IV {isNumber(leg.iv) && Number(leg.iv) > 0 ? `${num(leg.iv, 1)}%` : "NA"}
                        {" · "}Δ{" "}
                        {isNumber(leg.delta) && Number(leg.delta) !== 0 ? num(leg.delta, 2) : "NA"}
                    </p>
                </div>
            ) : (
                <p className="mt-1 text-sm text-dark-500">NA</p>
            )}
        </div>
    );
}

export function OptionSnapshotCard({ report }) {
    const options = report?.options;
    const call = options?.atm_call;
    const put = options?.atm_put;
    const straddle =
        call && put && isNumber(call.ltp) && isNumber(put.ltp)
            ? Number(call.ltp) + Number(put.ltp)
            : null;

    return (
        <Card
            title="ATM option snapshot"
            subtitle={
                options
                    ? `Strike ${whole(options.atm_strike)} · expiry ${options.expiry}`
                    : "At-the-money call and put"
            }
        >
            {!options ? (
                <Na>
                    Unavailable: needs a connected Zerodha session and an imported option catalogue.
                </Na>
            ) : (
                <>
                    <div className="grid grid-cols-2 gap-2">
                        <Leg title="Call (CE)" leg={call} />
                        <Leg title="Put (PE)" leg={put} />
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2">
                        <Stat
                            label="ATM straddle"
                            value={straddle === null ? "NA" : `₹${num(straddle)}`}
                        />
                        <Stat label="Put / call OI" value={num(options.pcr_oi, 2)} />
                    </div>
                    <p className="mt-2 text-xs text-dark-500">
                        Market data only. Delta is a sensitivity, not a chance of profit, and no
                        entry or exit is suggested.
                    </p>
                </>
            )}
        </Card>
    );
}

// ------------------------------------------------- Expiry & strike setup

export function OptionsSetupCard({ report }) {
    const options = report?.options;
    const call = options?.atm_call;
    const sameStrikePut = options?.atm_put;
    const matched = options?.matched_put;
    const differs = matched && Number(matched.strike) !== Number(options?.atm_strike);

    return (
        <Card
            title="Expiry & strike selection"
            subtitle="Nearest expiry · ATM call · put matched on premium"
        >
            {!options ? (
                <Na>Unavailable: needs a connected Zerodha session and an option catalogue.</Na>
            ) : (
                <>
                    <div className="grid grid-cols-3 gap-2">
                        <Stat label="Expiry" value={options.expiry || "NA"} />
                        <Stat
                            label="Days to expiry"
                            value={isNumber(options.dte) ? options.dte : "NA"}
                        />
                        <Stat label="Lot size" value={whole(options.lot_size)} />
                    </div>
                    <div className="mt-2 space-y-2">
                        <Stat
                            label={`ATM call · ${whole(options.atm_strike)} CE`}
                            value={call ? `₹${num(call.ltp)}` : "NA"}
                            hint={call?.trading_symbol}
                        />
                        <Stat
                            label="Premium-matched put"
                            value={
                                matched
                                    ? `${whole(matched.strike)} PE · ₹${num(matched.ltp)} · ${num(matched.premium_gap_pct, 1)}% off the call`
                                    : "No put within 15% of the call premium"
                            }
                            hint={matched?.trading_symbol}
                        />
                        <Stat
                            label={`Same-strike put · ${whole(options.atm_strike)} PE`}
                            value={sameStrikePut ? `₹${num(sameStrikePut.ltp)}` : "NA"}
                        />
                    </div>
                    {differs && (
                        <p className="mt-2 text-xs text-amber-300">
                            The matched put is at a different strike from the call, so it is a
                            different structure from a same-strike straddle.
                        </p>
                    )}
                </>
            )}
        </Card>
    );
}

// ------------------------------------------------------------ OI profile

export function OiProfileCard({ report }) {
    const options = report?.options;
    const walls = options?.oi_walls || {};
    const callWall = walls.call_wall;
    const putWall = walls.put_wall;

    return (
        <Card
            title="Open interest profile"
            subtitle="Where open contracts are concentrated · not buy or sell orders"
        >
            {!options ? (
                <Na>Unavailable: no option chain for this market.</Na>
            ) : (
                <div className="grid grid-cols-2 gap-2">
                    <Stat
                        label="Largest call OI (resistance)"
                        value={callWall ? `${whole(callWall.strike)} · ${lakh(callWall.oi)}` : "NA"}
                    />
                    <Stat
                        label="Largest put OI (support)"
                        value={putWall ? `${whole(putWall.strike)} · ${lakh(putWall.oi)}` : "NA"}
                    />
                    <Stat label="Put / call OI" value={num(options.pcr_oi, 2)} />
                    <Stat label="Max pain" value={whole(options.max_pain)} />
                </div>
            )}
        </Card>
    );
}
