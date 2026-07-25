import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Button } from "../../components/common";
import AnalysisForm from "./components/AnalysisForm";
import SignalCard from "./components/SignalCard";
import AIResponseView from "./components/AIResponseView";
import { analysisAPI } from "../../api/analysis";

export default function Analysis() {
    const [result, setResult] = useState(null);

    const { mutate: analyze, isPending } = useMutation({
        mutationFn: (data) => analysisAPI.analyze(data),
        onSuccess: (res) => setResult(res.data.data),
    });

    return (
        <PageWrapper
            title="AI Analysis"
            subtitle="AI-powered market analysis and setup detection"
            actions={

                href = "/analysis/history"
          className="text-xs text-primary-400 hover:text-primary-300"
        >
            View History →
        </a>
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
                <>
                    <SignalCard result={result} />
                    <AIResponseView response={result.reasoning} />
                </>
            ) : (
                <Card>
                    <div className="flex flex-col items-center justify-center
                              py-16 text-center">
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
    </PageWrapper >
  );
}