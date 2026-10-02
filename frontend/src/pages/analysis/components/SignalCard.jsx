import { Badge, Card } from "../../../components/common";
import { getSignalBadge, getConfidenceColor } from "../../../utils/helpers";
import { formatNumber } from "../../../utils/formatters";
import { Link } from "react-router-dom";

export default function SignalCard({ result }) {
    if (!result) return null;

    const badgeVariant =
        result.signal === "BUY" ? "green" :
            result.signal === "SELL" ? "red" : "gray";

    const straddleCandidate = result.volatility_setup?.eligible === true;
    const contract = straddleCandidate ? null : result.suggested_contract;

    return (
        <Card title="Athena’s read" subtitle="A decision aid based on the evidence shown below; it does not place an order.">
            {/* Suggested Trade — the actual "what to buy" answer, using the
                real contract StrikeSelectionService picked (real strike,
                real LTP) rather than just an index-level target/stop. */}
            {contract ? (
                <div className="p-4 bg-dark-800 rounded-lg border border-primary-500/40 mb-4">
                    <p className="text-xs text-dark-400 mb-1">Option to review</p>
                    <p className="text-lg font-bold text-dark-50">
                        {result.signal === "BUY" ? "Bullish view" : "Bearish view"} · Buy {contract.option_type} · {contract.trading_symbol}
                    </p>
                    <p className="mt-1 text-xs text-dark-400">
                        Athena’s direction maps to {contract.option_type === "CE" ? "a call (CE)" : "a put (PE)"}. Review the current contract price before taking any action; this result does not submit an order.
                    </p>
                    <div className="grid grid-cols-3 gap-3 mt-3 text-sm">
                        <div>
                            <p className="text-xs text-dark-600">Strike</p>
                            <p className="font-mono text-dark-200">
                                {formatNumber(contract.strike)} {contract.option_type}
                            </p>
                        </div>
                        <div>
                            <p className="text-xs text-dark-500">Premium at analysis</p>
                            <p className="font-mono text-dark-200">
                                ₹{formatNumber(contract.entry_premium)}
                            </p>
                        </div>
                        <div>
                            <p className="text-xs text-dark-600">Expiry</p>
                            <p className="font-mono text-dark-200">{contract.expiry}</p>
                        </div>
                    </div>
                    {result.session_id && contract.instrument_id && !["OPEN", "WAITING_EXIT", "CLOSED", "NEEDS_REVIEW"].includes(result.paper_evaluation?.status) && (
                        <Link
                            to={`/paper/orders?${new URLSearchParams({
                                analysis_session_id: String(result.session_id),
                                instrument_id: String(contract.instrument_id),
                                symbol: contract.trading_symbol,
                                quantity: String(contract.lot_size || 1),
                            }).toString()}`}
                            className="inline-flex mt-4 rounded-lg bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-500"
                        >
                            Simulate in Paper Trading
                        </Link>
                    )}
                </div>
            ) : (result.signal === "BUY" || result.signal === "SELL") && !straddleCandidate ? (
                <div className="p-3 bg-dark-800 rounded-lg mb-4">
                    <p className="text-sm text-dark-300">
                        Athena has a directional view, but couldn’t verify an option contract. Check the Zerodha connection and refresh the option chain before considering an order.
                    </p>
                </div>
            ) : null}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-dark-800 rounded-lg text-center">
                    <p className="text-xs text-dark-500 mb-2">Market stance</p>
                    <Badge variant={badgeVariant} className="text-sm px-3 py-1">
                        {result.signal === "BUY" ? "Bullish candidate" : result.signal === "SELL" ? "Bearish candidate" : "No Trade"}
                    </Badge>
                </div>
                <div className="p-3 bg-dark-800 rounded-lg text-center">
                    <p className="text-xs text-dark-500 mb-1">AI confidence · not win odds</p>
                    <p className={`text-xl font-bold font-mono
            ${getConfidenceColor(result.confidence_level)}`}>
                        {result.confidence == null ? "Unavailable" : `${result.confidence}%`}
                    </p>
                </div>
                {result.target && (
                    <div className="p-3 bg-dark-800 rounded-lg text-center">
                        <p className="text-xs text-dark-500 mb-1">Index Target</p>
                        <p className="text-lg font-bold text-green-400 font-mono">
                            {formatNumber(result.target)}
                        </p>
                    </div>
                )}
                {result.stop_loss && (
                    <div className="p-3 bg-dark-800 rounded-lg text-center">
                        <p className="text-xs text-dark-500 mb-1">Index Stop Loss</p>
                        <p className="text-lg font-bold text-red-400 font-mono">
                            {formatNumber(result.stop_loss)}
                        </p>
                    </div>
                )}
            </div>
            {result.no_trade_reason && <p className="text-sm text-dark-200 mt-4">No Trade: {result.no_trade_reason}</p>}
            {result.paper_evaluation && <div className="mt-4 p-3 border border-dark-700 rounded-lg text-sm text-dark-300"><p>Paper evaluation: {result.paper_evaluation.status}</p><p className="mt-1 text-xs">{result.paper_evaluation.reason}</p></div>}

            {/* Risks */}
            {result.risks?.length > 0 && (
                <div className="mt-4">
                    <p className="text-xs text-dark-500 mb-2">Risk Factors</p>
                    <div className="flex flex-wrap gap-2">
                        {result.risks.map((risk, i) => (
                            <Badge key={i} variant="yellow">{risk}</Badge>
                        ))}
                    </div>
                </div>
            )}

            {/* Validation warnings — visible when the output guard caught
                and stripped something, so this isn't silently invisible */}
            {result.validation_warnings?.length > 0 && (
                <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <p className="text-xs text-yellow-400 font-medium mb-1">
                        Output validation flagged {result.validation_warnings.length} issue(s)
                    </p>
                    <ul className="text-xs text-dark-400 space-y-1">
                        {result.validation_warnings.map((w, i) => (
                            <li key={i}>• {w}</li>
                        ))}
                    </ul>
                </div>
            )}

            {(result.provider || result.model) && (
                <div className="mt-4 pt-3 border-t border-dark-800 flex flex-wrap gap-x-5 gap-y-1 text-xs text-dark-500">
                    {result.provider && <span>AI provider: {result.provider}</span>}
                    {result.model && <span>Model: {result.model}</span>}
                </div>
            )}
        </Card>
    );
}
