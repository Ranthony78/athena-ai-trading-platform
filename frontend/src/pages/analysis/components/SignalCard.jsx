import { Badge, Card } from "../../../components/common";
import { getSignalBadge, getConfidenceColor } from "../../../utils/helpers";
import { formatNumber } from "../../../utils/formatters";

export default function SignalCard({ result }) {
    if (!result) return null;

    const badgeVariant =
        result.signal === "BUY" ? "green" :
            result.signal === "SELL" ? "red" : "gray";

    return (
        <Card title="Signal Result">
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
                        <p className="text-xs text-dark-500 mb-1">Target</p>
                        <p className="text-lg font-bold text-green-400 font-mono">
                            {formatNumber(result.target)}
                        </p>
                    </div>
                )}
                {result.stop_loss && (
                    <div className="p-3 bg-dark-800 rounded-lg text-center">
                        <p className="text-xs text-dark-500 mb-1">Stop Loss</p>
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
        </Card>
    );
}