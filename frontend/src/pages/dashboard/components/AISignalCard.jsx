import { Brain, Clock } from "lucide-react";
import { Card, Badge, EmptyState } from "../../../components/common";
import { formatRelativeTime } from "../../../utils/formatters";

export default function AISignalCard({ signals = [] }) {
    return (
        <Card title="AI Signals" subtitle="Today's AI-generated trading signals" actions={<a href="/analysis" className="text-xs text-primary-400 hover:text-primary-300">Run Analysis</a>}>
            {signals.length === 0 ? (
                <EmptyState icon={Brain} title="No signals today" description="Run an AI analysis to generate signals" />
            ) : (
                <div className="space-y-3">
                    {signals.slice(0, 5).map((signal) => (
                        <div key={signal.id} className="flex items-center justify-between p-3 bg-dark-800 rounded-lg">
                            <div className="flex items-center gap-3">
                                <Badge variant={signal.signal === "BUY" ? "green" : signal.signal === "SELL" ? "red" : "gray"}>{signal.signal}</Badge>
                                <div>
                                    <p className="text-sm font-medium text-dark-100">{signal.symbol}</p>
                                    <p className="text-xs text-dark-500">Confidence: {signal.confidence_score}%</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-1 text-dark-500 text-xs">
                                <Clock className="w-3 h-3" />
                                {formatRelativeTime(signal.signal_time)}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </Card>
    );
}
