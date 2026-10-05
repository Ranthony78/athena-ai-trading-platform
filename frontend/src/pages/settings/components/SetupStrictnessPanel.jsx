import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Card, Spinner } from "../../../components/common";
import { analysisAPI } from "../../../api/analysis";

const DESCRIPTIONS = {
    STRICT: "BUY/SELL only when the evidence clearly supports it. Most runs say No Trade.",
    BALANCED:
        "A BUY/SELL may appear when most of the evidence agrees, with lower confidence and the conflicts listed.",
    EXPLORATORY:
        "Gives its best directional candidate whenever the data is valid. Meant for paper forward testing.",
};

function messageOf(error) {
    return error?.response?.data?.message || "Could not save the setting. Please try again.";
}

// How readily the AI may return BUY/SELL instead of No Trade. Stale or missing
// quotes, a closed market and the 14:00 IST cut-off still force No Trade.
export default function SetupStrictnessPanel() {
    const queryClient = useQueryClient();
    const { data, isLoading, isError } = useQuery({
        queryKey: ["ai-preferences"],
        queryFn: () => analysisAPI.getPreferences(),
        select: (res) => res.data.data,
    });
    const save = useMutation({
        mutationFn: (setup_strictness) => analysisAPI.savePreferences({ setup_strictness }),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ai-preferences"] }),
    });

    return (
        <Card title="AI setup strictness" className="mt-4">
            <p className="text-xs text-dark-400 mb-3">
                Controls how readily the AI suggests a trade. Safety rules always apply: stale or
                missing prices, a closed market and times from 14:00 IST still give No Trade. Each
                saved run records the level used.
            </p>
            {isLoading && <Spinner />}
            {isError && <Alert type="error" message="Could not load the setting." />}
            {save.isError && <Alert type="error" message={messageOf(save.error)} />}
            {data && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3" role="radiogroup">
                    {data.options.map((option) => {
                        const active = data.setup_strictness === option.value;
                        return (
                            <button
                                key={option.value}
                                type="button"
                                role="radio"
                                aria-checked={active}
                                disabled={save.isPending}
                                onClick={() => !active && save.mutate(option.value)}
                                className={`text-left rounded-xl border p-3 transition-colors ${
                                    active
                                        ? "border-primary-500 bg-primary-900/30"
                                        : "border-dark-700 hover:border-dark-500"
                                }`}
                            >
                                <p className="text-sm font-semibold text-dark-100">
                                    {option.label}
                                    {active ? " · selected" : ""}
                                </p>
                                <p className="text-xs text-dark-400 mt-1">
                                    {DESCRIPTIONS[option.value]}
                                </p>
                            </button>
                        );
                    })}
                </div>
            )}
        </Card>
    );
}
