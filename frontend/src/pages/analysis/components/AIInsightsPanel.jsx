import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, Badge } from "../../../components/common";
import { formatNumber } from "../../../utils/formatters";

function ProbabilityCard({ probability }) {
    if (!probability || probability.upside_pct == null) {
        return (
            <Card title="Historical Move Baseline">
                <p className="text-sm text-dark-600">
                    {probability?.basis ||
                        "Unavailable — needs a verified, horizon-matched historical base rate."}
                </p>
            </Card>
        );
    }
    const bars = [
        {
            label: "Upward",
            value: probability.upside_pct,
            color: "text-green-400 border-green-500/40",
        },
        {
            label: "Downward",
            value: probability.downside_pct,
            color: "text-red-400 border-red-500/40",
        },
        {
            label: "Sideways",
            value: probability.sideways_pct,
            color: "text-dark-300 border-dark-600",
        },
    ];
    return (
        <Card
            title="Historical Move Baseline"
            subtitle={
                "Observed frequency · " +
                (probability.sample_size ?? "—") +
                " matched sessions" +
                (probability.low_confidence
                    ? " · limited sample"
                    : " · descriptive, not a prediction")
            }
        >
            <div className="grid grid-cols-3 gap-3">
                {bars.map((b) => (
                    <div key={b.label} className={`p-3 rounded-lg border text-center ${b.color}`}>
                        <p className="text-2xl font-bold font-mono">{b.value ?? "NA"}%</p>
                        <p className="text-xs text-dark-500 mt-1">{b.label}</p>
                    </div>
                ))}
            </div>
            {probability.basis && <p className="text-xs text-dark-500 mt-3">{probability.basis}</p>}
        </Card>
    );
}

function EvidenceValue({ label, value, detail, source, unavailableReason }) {
    const unavailable = value === null || value === undefined || value === "";
    return (
        <div className="rounded-lg border border-dark-700 bg-dark-900/40 p-3">
            <p className="text-[11px] uppercase tracking-wide text-dark-500">{label}</p>
            <p className="mt-1 text-sm font-semibold text-dark-100">
                {unavailable ? "Unavailable" : value}
            </p>
            {(detail || unavailableReason) && (
                <p className="mt-1 text-xs text-dark-400">
                    {unavailable ? unavailableReason : detail}
                </p>
            )}
            {source && <p className="mt-2 text-[10px] text-dark-600">Source: {source}</p>}
        </div>
    );
}

function RuleEvidenceCard({ evidence }) {
    if (!evidence) return null;
    const expected = evidence.expected_move || {};
    const premium = evidence.premium_hurdle || {};
    const momentum = evidence.momentum_band || {};
    const oi = evidence.oi_evidence || {};
    const volatility = evidence.volatility_context || {};
    const dailyMove = evidence.daily_move_comparison || {};
    const buyingAudit = evidence.option_buying_audit;
    const orb = evidence.opening_range || {};
    const cpr = evidence.cpr_context || {};
    const fmt = (value) =>
        value == null ? null : Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 });
    const prettyStatus = (value) => (value ? value.replaceAll("_", " ") : null);

    return (
        <Card
            title="Athena Evidence Checks"
            subtitle={`Deterministic context sent to the AI · ${evidence.version || "version unavailable"}${evidence.as_of ? ` · ${new Date(evidence.as_of).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} IST` : ""}`}
            className="lg:col-span-2"
        >
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                <EvidenceValue
                    label={`VIX-scaled 1σ move · ${expected.horizon_minutes ?? "—"} min`}
                    value={
                        expected.one_sigma_points == null
                            ? null
                            : `${fmt(expected.one_sigma_points)} pts`
                    }
                    detail={expected.basis}
                    source={expected.source}
                    unavailableReason={expected.reason}
                />
                <EvidenceValue
                    label="Daily implied vs observed move"
                    value={
                        dailyMove.experimental_daily_blend_points == null
                            ? null
                            : `${fmt(dailyMove.experimental_daily_blend_points)} pts · experimental daily blend`
                    }
                    detail={`VIX daily 1σ ${fmt(dailyMove.vix_daily_one_sigma_points) ?? "unavailable"} pts · mean absolute open-to-close ${fmt(dailyMove.historical_mean_absolute_open_close_points) ?? "unavailable"} pts · ${dailyMove.sample_size ?? 0}/15 sessions. ${dailyMove.note || ""}`}
                    source={dailyMove.source}
                    unavailableReason={
                        dailyMove.reason || "Daily comparison was not captured in this request."
                    }
                />
                <EvidenceValue
                    label="ATM premium comparison"
                    value={
                        premium.expected_move_points == null
                            ? null
                            : `Move ${fmt(premium.expected_move_points)} pts · reference ${premium.margin_multiple ?? 1.15}× premium`
                    }
                    detail={`Call: ${premium.call?.threshold_points == null ? "unavailable" : `${fmt(premium.call.threshold_points)} pt reference (${prettyStatus(premium.call.status)})`} · Put: ${premium.put?.threshold_points == null ? "unavailable" : `${fmt(premium.put.threshold_points)} pt reference (${prettyStatus(premium.put.status)})`}. Comparison only, not expected profit.`}
                    source={premium.source}
                    unavailableReason="Needs verified ATM option LTPs and a VIX-scaled move estimate."
                />
                <EvidenceValue
                    label="Move from open vs reference band"
                    value={
                        momentum.move_from_open_points == null
                            ? null
                            : `${prettyStatus(momentum.direction)} ${fmt(momentum.move_from_open_points)} pts · ${prettyStatus(momentum.status)}`
                    }
                    detail={
                        momentum.fraction_of_daily_one_sigma == null
                            ? null
                            : `${(momentum.fraction_of_daily_one_sigma * 100).toFixed(1)}% of daily 1σ; reference ${(momentum.reference_min * 100).toFixed(0)}–${(momentum.reference_max * 100).toFixed(0)}%. Context only.`
                    }
                    source={momentum.source}
                    unavailableReason={momentum.reason}
                />
                <EvidenceValue
                    label="OI build-up / unwind"
                    value={
                        oi.status === "unavailable"
                            ? oi.current_pcr_oi == null
                                ? null
                                : `Change unavailable · current PCR ${oi.current_pcr_oi}`
                            : prettyStatus(oi.status)
                    }
                    detail={oi.reason}
                    source={oi.source}
                />
                <EvidenceValue
                    label="Relative volatility context"
                    value={
                        volatility.scaled_context_pct == null
                            ? null
                            : `${volatility.scaled_context_pct}/100 · ratio ${volatility.ratio}`
                    }
                    detail={
                        volatility.status === "unavailable"
                            ? null
                            : `${fmt(volatility.daily_one_sigma_points)} pt daily 1σ vs ${fmt(volatility.historical_median_full_session_range_points)} pt historical median session range · ${volatility.note}`
                    }
                    source={volatility.source}
                    unavailableReason={volatility.reason}
                />
                <EvidenceValue
                    label="Opening 15-minute range"
                    value={
                        orb.status === "unavailable"
                            ? null
                            : `${prettyStatus(orb.status)} · ${fmt(orb.low)}–${fmt(orb.high)}`
                    }
                    detail={orb.note}
                    source={orb.source}
                    unavailableReason={orb.reason}
                />
                <EvidenceValue
                    label="CPR width context"
                    value={
                        cpr.status === "unavailable"
                            ? null
                            : `${prettyStatus(cpr.status)} · ${cpr.width_as_pct_of_prior_day_range}% of prior range`
                    }
                    detail={
                        cpr.status === "unavailable"
                            ? null
                            : `Recent median ${cpr.recent_median_width_pct}% · ${cpr.sample_size} comparison sessions · reference ${cpr.reference_date}`
                    }
                    source={cpr.source}
                    unavailableReason={cpr.reason}
                />
            </div>
            {buyingAudit && (
                <details className="mt-4 rounded-lg border border-dark-700 p-3" open>
                    <summary className="cursor-pointer text-sm font-semibold text-dark-100">
                        ATM option-buying research · input audit
                    </summary>
                    <div className="grid gap-3 sm:grid-cols-3 mt-3">
                        <EvidenceValue
                            label="ATM straddle mid"
                            value={
                                buyingAudit.straddle_mid_points == null
                                    ? null
                                    : `${fmt(buyingAudit.straddle_mid_points)} pts`
                            }
                            unavailableReason="Requires valid bid/ask quotes for both legs."
                        />
                        <EvidenceValue
                            label="Combined ask debit"
                            value={
                                buyingAudit.straddle_ask_debit_points == null
                                    ? null
                                    : `${fmt(buyingAudit.straddle_ask_debit_points)} pts`
                            }
                            unavailableReason="Requires valid bid/ask quotes for both legs."
                        />
                        <EvidenceValue
                            label={`VIX 1σ · ${buyingAudit.horizon_minutes} min`}
                            value={
                                buyingAudit.vix_horizon_one_sigma_points == null
                                    ? null
                                    : `${fmt(buyingAudit.vix_horizon_one_sigma_points)} pts`
                            }
                            detail="Statistical reference, not expected profit."
                        />
                    </div>
                    <div className="mt-3 space-y-2">
                        {buyingAudit.filters.map((filter) => (
                            <div
                                key={filter.key}
                                className="rounded-lg border border-dark-700 p-3 text-xs"
                            >
                                <p className="font-semibold text-dark-200">
                                    {filter.key} · {filter.label} ·{" "}
                                    {filter.status.replaceAll("_", " ")}
                                </p>
                                <p className="mt-1 text-dark-400">{filter.reason}</p>
                            </div>
                        ))}
                    </div>
                    <p className="mt-3 text-xs text-dark-400">{buyingAudit.note}</p>
                </details>
            )}
            <p className="mt-3 text-xs text-dark-500">
                {evidence.disclaimer} Numeric forecast probabilities remain the verified historical
                baseline and are not adjusted by these checks.
            </p>
        </Card>
    );
}

function ForecastLearningCard({ tracking, calibration, paperTrades, model, promptVersion }) {
    if (!tracking && !calibration && !paperTrades && !model && !promptVersion) return null;
    const status = tracking?.status;
    const statusText =
        status === "PENDING"
            ? "Outcome tracking pending"
            : status === "RESOLVED"
              ? "Resolved " + (tracking.actual_class ?? "")
              : status === "INSUFFICIENT_DATA"
                ? "Outcome unavailable — Athena could not find a usable target candle and probability snapshot"
                : "Historical only — no live outcome tracking";
    return (
        <Card title="Forecast Outcome & Calibration">
            <div className="space-y-2 text-sm">
                {(model || promptVersion) && (
                    <div className="flex justify-between gap-4">
                        <span className="text-dark-500">AI model / prompt</span>
                        <span className="font-mono text-dark-200">
                            {model ?? "—"} / {promptVersion ?? "—"}
                        </span>
                    </div>
                )}
                {tracking && (
                    <>
                        <div className="flex justify-between gap-4">
                            <span className="text-dark-500">Forecast horizon</span>
                            <span className="font-mono text-dark-200">
                                {tracking.horizon_minutes} min
                            </span>
                        </div>
                        <div className="flex justify-between gap-4">
                            <span className="text-dark-500">Starting index price</span>
                            <span className="font-mono text-dark-200">
                                {tracking.anchor_price ?? "NA"}
                            </span>
                        </div>
                        <p className="text-xs text-dark-500">{statusText}</p>
                        {status === "RESOLVED" && (
                            <>
                                <div className="flex justify-between gap-4">
                                    <span className="text-dark-500">Observed index price</span>
                                    <span className="font-mono text-dark-200">
                                        {tracking.outcome_price ?? "—"}
                                    </span>
                                </div>
                                <div className="flex justify-between gap-4">
                                    <span className="text-dark-500">Forecast Brier score</span>
                                    <span className="font-mono text-dark-200">
                                        {tracking.brier_score ?? "—"}
                                    </span>
                                </div>
                            </>
                        )}
                    </>
                )}
                {calibration && (
                    <>
                        <div className="border-t border-dark-800 pt-2 flex justify-between gap-4">
                            <span className="text-dark-500">Resolved forecast sample</span>
                            <span className="font-mono text-dark-200">
                                {calibration.sample_size ?? 0}
                            </span>
                        </div>
                        <div className="flex justify-between gap-4">
                            <span className="text-dark-500">Mean 3-class Brier score</span>
                            <span className="font-mono text-dark-200">
                                {calibration.mean_brier_score ?? "Not ready"}
                            </span>
                        </div>
                        <div className="flex justify-between gap-4">
                            <span className="text-dark-500">Top-class direction accuracy</span>
                            <span className="font-mono text-dark-200">
                                {calibration.top_class_accuracy_pct == null
                                    ? "Not ready"
                                    : `${calibration.top_class_accuracy_pct}%`}
                            </span>
                        </div>
                        <p className="text-xs text-dark-500">
                            Lower is better; uniform-probability reference is 0.667.{" "}
                            {calibration.low_confidence
                                ? "Fewer than " +
                                  (calibration.min_sample_for_confidence ?? 10) +
                                  " resolved forecasts; treat as early data."
                                : "Based on completed horizon outcomes."}
                        </p>
                    </>
                )}
                {paperTrades && (
                    <div className="border-t border-dark-800 pt-3 space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-dark-400">
                            Linked paper-trade results
                        </p>
                        <div className="flex justify-between gap-4">
                            <span className="text-dark-500">Completed linked trades</span>
                            <span className="font-mono text-dark-200">
                                {paperTrades.sample_size ?? 0}
                            </span>
                        </div>
                        {(paperTrades.sample_size ?? 0) > 0 && (
                            <>
                                <div className="flex justify-between gap-4">
                                    <span className="text-dark-500">Net profitable trades</span>
                                    <span className="font-mono text-dark-200">
                                        {paperTrades.net_win_rate_pct}%
                                    </span>
                                </div>
                                <div className="flex justify-between gap-4">
                                    <span className="text-dark-500">Mean net P&amp;L</span>
                                    <span className="font-mono text-dark-200">
                                        ₹{formatNumber(paperTrades.mean_net_pnl)}
                                    </span>
                                </div>
                            </>
                        )}
                        <p className="text-xs text-dark-500">
                            {paperTrades.note}{" "}
                            {paperTrades.low_confidence &&
                                "Small sample — treat as early evidence."}
                            {paperTrades.automatic_model_updates === false &&
                                " Athena records results; it does not automatically change prompts or model behavior."}
                        </p>
                    </div>
                )}
            </div>
        </Card>
    );
}

function SentimentCard({ sentiment }) {
    if (!sentiment || !sentiment.classification) {
        return (
            <Card title="Market Sentiment">
                <p className="text-sm text-dark-600">
                    Unavailable — needs VIX, breadth, or news data (Sections 1/4/5 were NA for this
                    analysis).
                </p>
            </Card>
        );
    }
    const variant = sentiment.classification?.toLowerCase().includes("bull")
        ? "green"
        : sentiment.classification?.toLowerCase().includes("bear")
          ? "red"
          : "gray";
    return (
        <Card title="Market Sentiment">
            <div className="flex items-center justify-between mb-3">
                <Badge variant={variant}>{sentiment.classification}</Badge>
                {sentiment.confidence_pct != null && (
                    <span className="text-sm font-mono text-dark-300">
                        {sentiment.confidence_pct}% confidence
                    </span>
                )}
            </div>
            {sentiment.key_reasons?.length > 0 && (
                <ul className="text-sm text-dark-300 space-y-1 mb-3">
                    {sentiment.key_reasons.map((r, i) => (
                        <li key={i}>• {r}</li>
                    ))}
                </ul>
            )}
            {sentiment.basis && <p className="text-xs text-dark-500">{sentiment.basis}</p>}
        </Card>
    );
}

function OptionComparisonCard({ comparison }) {
    if (!comparison) {
        return (
            <Card title="ATM Option Comparison">
                <p className="text-sm text-dark-600">
                    Option delta unavailable — needs verified option Greeks. The real ATM strike and
                    expiry are still shown in the "ATM Option Analysis" card further down this page.
                </p>
            </Card>
        );
    }
    return (
        <Card
            title="ATM Option Comparison"
            subtitle="Delta sensitivity · not a probability of profit"
        >
            <div className="grid grid-cols-2 gap-3">
                <div
                    className={`p-3 rounded-lg border text-center ${comparison.stronger_side === "CALL" ? "border-green-500/40 bg-green-500/5" : "border-dark-700"}`}
                >
                    <p className="text-xs text-dark-500 mb-1">CALL</p>
                    <p className="text-xl font-bold font-mono text-green-400">
                        {comparison.call_delta ?? "N/A"}
                    </p>
                    {comparison.stronger_side === "CALL" && (
                        <Badge variant="green" className="mt-2">
                            Stronger side
                        </Badge>
                    )}
                </div>
                <div
                    className={`p-3 rounded-lg border text-center ${comparison.stronger_side === "PUT" ? "border-red-500/40 bg-red-500/5" : "border-dark-700"}`}
                >
                    <p className="text-xs text-dark-500 mb-1">PUT</p>
                    <p className="text-xl font-bold font-mono text-red-400">
                        {comparison.put_delta ?? "N/A"}
                    </p>
                    {comparison.stronger_side === "PUT" && (
                        <Badge variant="red" className="mt-2">
                            Stronger side
                        </Badge>
                    )}
                </div>
            </div>
            {comparison.basis && <p className="text-xs text-dark-500 mt-3">{comparison.basis}</p>}
        </Card>
    );
}

function PriceExpectationCard({ expectation }) {
    if (!expectation) {
        return (
            <Card title="Price Expectation">
                <p className="text-sm text-dark-600">
                    Unavailable — needs CPR/Pivot/ATR data for this analysis.
                </p>
            </Card>
        );
    }
    const rows = [
        ["Nearest Support", expectation.nearest_support],
        ["Nearest Resistance", expectation.nearest_resistance],
        ["Historical Excursion Low", expectation.expected_range_low],
        ["Historical Excursion High", expectation.expected_range_high],
    ];
    return (
        <Card title="Price Expectation">
            <div className="space-y-2">
                {rows.map(([label, value]) => (
                    <div key={label} className="flex justify-between text-sm">
                        <span className="text-dark-500">{label}</span>
                        <span className="font-mono text-dark-200">
                            {formatNumber(value) ?? "NA"}
                        </span>
                    </div>
                ))}
            </div>
            {expectation.basis && <p className="text-xs text-dark-500 mt-3">{expectation.basis}</p>}
        </Card>
    );
}

function SessionStructureCard({ structure }) {
    if (!structure || structure.length === 0) {
        return (
            <Card title="Today's Realized Session Structure">
                <p className="text-sm text-dark-600">
                    Unavailable — needs live intraday candle data.
                </p>
            </Card>
        );
    }

    const referenceDate = structure.find((b) => b.reference_date)?.reference_date;

    return (
        <Card
            title="Today's Realized Session Structure"
            subtitle={
                referenceDate
                    ? `Today hasn't started — showing ${referenceDate} for reference`
                    : "What actually happened per window — not a prediction"
            }
        >
            {referenceDate && (
                <div className="mb-3 px-3 py-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <p className="text-xs text-yellow-400">
                        Market hasn't opened today yet. The blocks below are from the most recent
                        completed session ({referenceDate}), not today.
                    </p>
                </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {structure.map((b) => {
                    if (b.status === "NOT_STARTED") {
                        return (
                            <div key={b.window} className="p-3 bg-dark-800 rounded-lg opacity-50">
                                <p className="text-xs text-dark-500 mb-1">{b.window}</p>
                                <p className="text-sm text-dark-600">Not started yet</p>
                            </div>
                        );
                    }
                    if (b.status === "NO_DATA") {
                        return (
                            <div key={b.window} className="p-3 bg-dark-800 rounded-lg">
                                <p className="text-xs text-dark-500 mb-1">{b.window}</p>
                                <p className="text-sm text-dark-600">No candle data</p>
                            </div>
                        );
                    }
                    const Icon =
                        b.direction === "Up"
                            ? TrendingUp
                            : b.direction === "Down"
                              ? TrendingDown
                              : Minus;
                    const color =
                        b.direction === "Up"
                            ? "text-green-400"
                            : b.direction === "Down"
                              ? "text-red-400"
                              : "text-dark-400";
                    return (
                        <div key={b.window} className="p-3 bg-dark-800 rounded-lg">
                            <div className="flex items-center justify-between mb-1">
                                <p className="text-xs text-dark-500">{b.window}</p>
                                {b.status === "IN_PROGRESS" && (
                                    <Badge variant="gray" className="text-[10px]">
                                        In progress
                                    </Badge>
                                )}
                            </div>
                            <div className="flex items-center gap-1">
                                <Icon className={`w-3.5 h-3.5 ${color}`} />
                                <span className={`text-sm font-mono ${color}`}>
                                    {b.move_pts > 0 ? "+" : ""}
                                    {b.move_pts} pts
                                </span>
                            </div>
                            <p className="text-xs text-dark-600 mt-1">Range: {b.range_pts} pts</p>
                        </div>
                    );
                })}
            </div>
        </Card>
    );
}

export default function AIInsightsPanel({ result }) {
    if (!result) return null;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ProbabilityCard probability={result.probability} />
            <SentimentCard sentiment={result.sentiment} />
            <OptionComparisonCard comparison={result.option_comparison} />
            <PriceExpectationCard expectation={result.price_expectation} />
            <RuleEvidenceCard evidence={result.rule_evidence} />
            <div className="lg:col-span-2">
                <SessionStructureCard structure={result.session_structure} />
            </div>
            <div className="lg:col-span-2">
                <ForecastLearningCard
                    tracking={result.forecast_tracking}
                    calibration={result.forecast_calibration}
                    paperTrades={result.paper_trade_learning}
                    model={result.model}
                    promptVersion={result.prompt_version}
                />
            </div>
        </div>
    );
}
