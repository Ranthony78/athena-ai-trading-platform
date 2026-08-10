import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button } from "../../components/common";
import AnalysisForm from "./components/AnalysisForm";
import SignalCard from "./components/SignalCard";
import AIResponseView from "./components/AIResponseView";
import { analysisAPI } from "../../api/analysis";

// Map known backend error substrings to a clearer, user-facing message.
// Falls back to the raw error text if nothing matches.
function friendlyErrorMessage(rawError) {
    if (!rawError) return null;

    const lower = rawError.toLowerCase();

    if (lower.includes("credit balance is too low")) {
        return "Your Anthropic API account has no usable credit balance. Add credits or claim a trial credit at console.anthropic.com, then try again.";
    }
    if (lower.includes("anthropic_api_key not set")) {
        return "No Anthropic API key is configured on the backend. Add ANTHROPIC_API_KEY to your .env file and restart the server.";
    }
    if (lower.includes("401") || lower.includes("authentication")) {
        return "The Anthropic API rejected the request as unauthenticated. Check that your API key is valid.";
    }
    if (lower.includes("rate limit") || lower.includes("429")) {
        return "The Anthropic API rate limit was hit. Wait a moment and try again.";
    }
    if (lower.includes("live data not available") || lower.includes("no candle data")) {
        return "No market data is available for this symbol yet, so no analysis could be run.";
    }

    return rawError;
}

function ErrorBanner({ error }) {
    const message = friendlyErrorMessage(error);
    if (!message) return null;

    return (
        <Card>
            <div className="flex items-start gap-3 p-1">
                <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                    <p className="text-sm font-medium text-red-400">
                        Analysis failed
                    </p>
                    <p className="text-sm text-dark-300 mt-1">
                        {message}
                    </p>
                </div>
            </div>
        </Card>
    );
}

export default function Analysis() {
    const [result, setResult] = useState(null);

    const { mutate: analyze, isPending } = useMutation({
        mutationFn: (data) => analysisAPI.analyze(data),
        onSuccess: (res) => setResult(res.data.data),
    });

    const hasError = Boolean(result?.error);

    return (
        <PageWrapper
            title="AI Analysis"
            subtitle="AI-powered market analysis and setup detection"
            actions={
                <div className="flex items-center gap-4">
                    <a
                        href="/analysis/report"
                        className="text-xs text-primary-400 hover:text-primary-300"
                    >
                        Full Report
                    </a>
                    <a
                        href="/analysis/history"
                        className="text-xs text-primary-400 hover:text-primary-300"
                    >
                        View History
                    </a>
                </div>
            }
        >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Form */}
                <div>
                    <AnalysisForm onSubmit={analyze} loading={isPending} />
                </div>

                {/* Result */}
                <div className="lg:col-span-2 space-y-4">
                    {result ? (
                        hasError ? (
                            <ErrorBanner error={result.error} />
                        ) : (
                            <>
                                <SignalCard result={result} />
                                <AIResponseView response={result.reasoning} />
                            </>
                        )
                    ) : (
                        <Card>
                            <div className="flex flex-col items-center justify-center py-16 text-center">
                                <p className="text-dark-400 text-sm">
                                    Run an analysis to see results
                                </p>
                                <p className="text-dark-600 text-xs mt-1">
                                    Select a symbol and timeframe, then click Analyze
                                </p>
                            </div>
                        </Card>
                    )}
                </div>
            </div>
        </PageWrapper>
    );
}
