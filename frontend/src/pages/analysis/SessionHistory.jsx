import { useQuery } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Table, Badge, Spinner } from "../../components/common";
import { analysisAPI } from "../../api/analysis";
import { formatDateTime } from "../../utils/formatters";

export default function SessionHistory() {
    const { data: sessions, isLoading } = useQuery({
        queryKey: ["ai-sessions"],
        queryFn: () => analysisAPI.getSessions(),
        select: (res) => res.data.data,
    });

    const columns = [
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
            key: "session_time",
            label: "Time",
            render: (val) => formatDateTime(val),
        },
    ];

    return (
        <PageWrapper title="Analysis History" subtitle="Past AI analysis sessions">
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
        </PageWrapper>
    );
}