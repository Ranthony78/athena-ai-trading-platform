import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Trash2 } from "lucide-react";
import { SavedRequest } from "./components/WorkspaceLearning";
import { PageWrapper } from "../../components/layout";
import { Card, Table, Badge, Spinner, Modal, Button } from "../../components/common";
import { analysisAPI } from "../../api/analysis";
import { formatDateTime } from "../../utils/formatters";

export default function SessionHistory() {
    const [selected, setSelected] = useState(null);
    const [confirmClear, setConfirmClear] = useState(false);
    const [actionMessage, setActionMessage] = useState(null);
    const queryClient = useQueryClient();
    const { data: sessions, isLoading } = useQuery({
        queryKey: ["ai-sessions"],
        queryFn: () => analysisAPI.getSessions(),
        select: (res) => res.data.data,
    });
    const clearHistory = useMutation({
        mutationFn: () => analysisAPI.clearSessions(),
        onSuccess: (response) => {
            setActionMessage(
                `Removed ${response.data.data.sessions_deleted} saved analysis sessions.`
            );
            setConfirmClear(false);
            setSelected(null);
            queryClient.invalidateQueries({ queryKey: ["ai-sessions"] });
        },
        onError: (error) => {
            setActionMessage(error.response?.data?.message || "Could not clear analysis history.");
        },
    });

    const columns = [
        {
            key: "id",
            label: "Request",
            render: (val) => (
                <button className="text-primary-400 underline" onClick={() => setSelected(val)}>
                    Inspect #{val}
                </button>
            ),
        },
        { key: "symbol", label: "Symbol" },
        { key: "session_type", label: "Type" },
        {
            key: "status",
            label: "Status",
            render: (val) => (
                <Badge variant={val === "COMPLETE" ? "green" : val === "FAILED" ? "red" : "gray"}>
                    {val}
                </Badge>
            ),
        },
        { key: "model_used", label: "Model" },
        { key: "tokens_used", label: "Tokens" },
        {
            key: "parsed_output",
            label: "Decision",
            render: (value) =>
                ["NO_SETUP", "NEUTRAL", "WATCH"].includes(value?.signal)
                    ? "No Trade"
                    : value?.signal || "Unavailable",
        },
        {
            key: "forecast_actual_class",
            label: "Observed move",
            render: (value) => value || "Unresolved",
        },
        {
            key: "paper_evaluation",
            label: "Paper",
            render: (value) => value?.status || "Not requested",
        },
        {
            key: "session_time",
            label: "Time",
            render: (val) => formatDateTime(val),
        },
    ];

    return (
        <PageWrapper
            title="Analysis History"
            subtitle="Your latest 200 saved sessions, including No Trade and failed requests"
            actions={
                sessions?.length > 0 && (
                    <Button
                        variant="danger"
                        size="sm"
                        icon={Trash2}
                        onClick={() => {
                            setActionMessage(null);
                            setConfirmClear(true);
                        }}
                    >
                        Clear history
                    </Button>
                )
            }
        >
            {actionMessage && (
                <p role="status" className="mb-3 text-sm text-dark-300">
                    {actionMessage}
                </p>
            )}
            <Card padding={false}>
                {isLoading ? (
                    <Spinner />
                ) : (
                    <Table
                        columns={columns}
                        data={sessions || []}
                        emptyTitle="No sessions yet"
                        emptyDescription="Run an analysis to see history"
                    />
                )}
            </Card>
            {selected && (
                <Card title={`Saved analysis #${selected}`}>
                    <SavedRequest key={selected} sessionId={selected} />
                </Card>
            )}
            <Modal
                isOpen={confirmClear}
                onClose={() => !clearHistory.isPending && setConfirmClear(false)}
                title="Permanently clear analysis history"
            >
                <p className="text-sm text-dark-300">
                    This permanently deletes all saved AI analysis sessions for your account and
                    their linked AI signal records. Paper orders, positions, and trades are kept,
                    but their links to these analyses are removed.
                </p>
                {clearHistory.isError && (
                    <p role="alert" className="mt-3 text-sm text-red-400">
                        {clearHistory.error?.response?.data?.message ||
                            "Could not clear analysis history."}
                    </p>
                )}
                <div className="flex justify-end gap-2 mt-6">
                    <Button
                        variant="secondary"
                        disabled={clearHistory.isPending}
                        onClick={() => setConfirmClear(false)}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="danger"
                        icon={Trash2}
                        loading={clearHistory.isPending}
                        onClick={() => clearHistory.mutate()}
                    >
                        Delete saved history
                    </Button>
                </div>
            </Modal>
        </PageWrapper>
    );
}
