import { Badge, Card } from "../../../components/common";
import { getSignalBadge, getConfidenceColor } from "../../../utils/helpers";
import { formatNumber } from "../../../utils/formatters";

export default function SignalCard({ result }) {
    if (!result) return null;

    const badgeVariant =
        result.signal === "BUY" ? "green" :
            result.signal === "SELL" ? "red" : "gray";

    const contract = result.suggested_contract;

    return (
        <Card title="Signal Result">
            {/* Suggested Trade — the actual "what to buy" answer, using the
                real contract StrikeSelectionService picked (real strike,
                real LTP) rather than just an index-level target/stop. */}
            {contract ? (
                <div className="p-4 bg-dark-800 rounded-lg border border-primary-500/40 mb-4">
                    <p className="text-xs text-dark-500 mb-1">Suggested Trade</p>
                    <p className="text-lg font-bold text-dark-50">
                        {result.signal} {contract.trading_symbol}
                    </p>
                    <div className="grid grid-cols-3 gap-3 mt-3 text-sm">
                        <div>
                            <p className="text-xs text-dark-600">Strike</p>
                            <p className="font-mono text-dark-200">
                                {formatNumber(contract.strike)} {contract.option_type}
                            </p>
                        </div>
                        <div>
                            <p className="text-xs text-dark-600">Entry Premium</p>
                            <p className="font-mono text-dark-200">
                                ₹{formatNumber(contract.entry_premium)}
                            </p>
                        </div>
                        <div>
                            <p className="text-xs text-dark-600">Expiry</p>
                            <p className="font-mono text-dark-200">{contract.expiry}</p>
                        </div>
                    </div>
                </div>
            ) : (result.signal === "BUY" || result.signal === "SELL") ? (
                <div className="p-3 bg-dark-800 rounded-lg mb-4">
                    <p className="text-xs text-dark-500">
                        No contract could be selected for this signal — check your
                        Zerodha connection and option chain data.
                    </p>
                </div>
            ) : null}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-dark-800 rounded-lg text-center">
                    <p className="text-xs text-dark-500 mb-2">Signal</p>
                    <Badge variant={badgeVariant} className="text-sm px-3 py-1">
                        {result.signal}
                    </Badge>
                </div>
                <div className="p-3 bg-dark-800 rounded-lg text-center">
                    <p className="text-xs text-dark-500 mb-1">Confidence</p>
                    <p className={`text-xl font-bold font-mono
            ${getConfidenceColor(result.confidence_level)}`}>
                        {result.confidence}%
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
        </Card>
    );
}