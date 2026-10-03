import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
    Activity,
    CheckCircle2,
    Cpu,
    KeyRound,
    RefreshCw,
    Save,
    Trash2,
    XCircle,
} from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Alert, Button, Card, Input, Spinner } from "../../components/common";
import { aiConnectionAPI } from "../../api/aiConnection";

const PROVIDERS = [
    { value: "gemini", label: "Google Gemini" },
    { value: "kimi", label: "Kimi (Moonshot)" },
    { value: "claude", label: "Anthropic Claude" },
    { value: "groq", label: "Groq" },
];

function errorMessage(error) {
    return (
        error?.response?.data?.message ||
        "The AI provider request failed. Check the backend and provider configuration."
    );
}

export default function AIConnection() {
    const queryClient = useQueryClient();
    const [selectedProvider, setSelectedProvider] = useState("gemini");
    const [apiKey, setApiKey] = useState("");
    const [feedback, setFeedback] = useState(null);
    const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
        queryKey: ["ai-provider-connection"],
        queryFn: () => aiConnectionAPI.getStatus(),
        select: (response) => response.data.data,
    });

    useEffect(() => {
        if (data?.provider && PROVIDERS.some((item) => item.value === data.provider)) {
            setSelectedProvider(data.provider);
        }
    }, [data?.provider]);

    const save = useMutation({
        mutationFn: () =>
            aiConnectionAPI.saveCredentials({ provider: selectedProvider, api_key: apiKey.trim() }),
        onSuccess: async (response) => {
            setApiKey("");
            setFeedback({ type: "success", message: response.data.message });
            await queryClient.invalidateQueries({ queryKey: ["ai-provider-connection"] });
        },
        onError: (requestError) =>
            setFeedback({ type: "error", message: errorMessage(requestError) }),
    });
    const test = useMutation({
        mutationFn: () => aiConnectionAPI.testConnection(),
        onSuccess: (response) =>
            setFeedback({
                type: "success",
                message: `${response.data.message} ${response.data.data.response_time_ms ?? "—"} ms · ${response.data.data.verified_model}`,
            }),
        onError: (requestError) =>
            setFeedback({ type: "error", message: errorMessage(requestError) }),
    });
    const remove = useMutation({
        mutationFn: () => aiConnectionAPI.removeCredentials(),
        onSuccess: async (response) => {
            setFeedback({ type: "success", message: response.data.message });
            await queryClient.invalidateQueries({ queryKey: ["ai-provider-connection"] });
        },
        onError: (requestError) =>
            setFeedback({ type: "error", message: errorMessage(requestError) }),
    });

    if (isLoading) return <Spinner />;

    return (
        <PageWrapper
            title="AI Connection"
            subtitle="Connect your own AI provider key. Athena stores it encrypted and never displays it again."
        >
            {isError ? (
                <div className="space-y-3">
                    <Alert type="error" message={errorMessage(error)} />
                    <Button
                        variant="secondary"
                        icon={RefreshCw}
                        loading={isFetching}
                        onClick={() => refetch()}
                    >
                        Retry Provider Status
                    </Button>
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                        <Card title="Provider Status">
                            <div className="mb-5 flex items-center gap-3">
                                {data?.configured ? (
                                    <CheckCircle2 className="h-8 w-8 text-green-400" />
                                ) : (
                                    <XCircle className="h-8 w-8 text-red-400" />
                                )}
                                <div>
                                    <p
                                        className={`text-lg font-bold ${data?.configured ? "text-green-400" : "text-red-400"}`}
                                    >
                                        {data?.is_mock
                                            ? "Development mock"
                                            : data?.configured
                                              ? "Configured"
                                              : "No key configured"}
                                    </p>
                                    <p className="text-sm text-dark-400">{data?.provider_name}</p>
                                </div>
                            </div>
                            <div className="space-y-3 text-sm">
                                <div className="flex items-center justify-between gap-3">
                                    <span className="inline-flex items-center gap-2 text-dark-400">
                                        <Cpu className="h-4 w-4" /> Provider / model
                                    </span>
                                    <span className="text-right text-dark-100">
                                        {data?.provider_name} / {data?.model}
                                    </span>
                                </div>
                                <div className="flex items-center justify-between gap-3">
                                    <span className="inline-flex items-center gap-2 text-dark-400">
                                        <KeyRound className="h-4 w-4" /> Credential
                                    </span>
                                    <span className="text-right text-dark-100">
                                        {data?.credential_source === "personal"
                                            ? "Personal key saved · encrypted"
                                            : data?.credential_source === "server"
                                              ? "Shared server key"
                                              : data?.is_mock
                                                ? "Not required"
                                                : "Not configured"}
                                    </span>
                                </div>
                            </div>
                            {feedback && (
                                <div className="mt-4">
                                    <Alert type={feedback.type} message={feedback.message} />
                                </div>
                            )}
                        </Card>

                        <Card title="Connect a Provider">
                            <div className="space-y-4">
                                <div>
                                    <label htmlFor="ai-provider" className="label">
                                        AI provider
                                    </label>
                                    <select
                                        id="ai-provider"
                                        className="input"
                                        value={selectedProvider}
                                        onChange={(event) => {
                                            setSelectedProvider(event.target.value);
                                            setFeedback(null);
                                        }}
                                    >
                                        {PROVIDERS.map((provider) => (
                                            <option key={provider.value} value={provider.value}>
                                                {provider.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <Input
                                    label={
                                        data?.personal_credential_saved
                                            ? "Replace API Key"
                                            : "API Key"
                                    }
                                    type="password"
                                    autoComplete="new-password"
                                    value={apiKey}
                                    onChange={(event) => {
                                        setApiKey(event.target.value);
                                        setFeedback(null);
                                    }}
                                    placeholder={
                                        data?.personal_credential_saved
                                            ? "Enter a new key to replace the saved key"
                                            : "Paste your provider API key"
                                    }
                                />
                                <p className="text-xs leading-5 text-dark-400">
                                    The key is sent over your authenticated connection, encrypted
                                    before database storage, and never included in API responses or
                                    logs.
                                </p>
                                <Button
                                    variant="primary"
                                    icon={Save}
                                    loading={save.isPending}
                                    disabled={!apiKey.trim() || apiKey.trim().length < 8}
                                    onClick={() => save.mutate()}
                                    className="w-full"
                                >
                                    Save Provider Key
                                </Button>
                                {data?.personal_credential_saved && (
                                    <Button
                                        variant="danger"
                                        icon={Trash2}
                                        loading={remove.isPending}
                                        onClick={() => remove.mutate()}
                                        className="w-full"
                                    >
                                        Remove Personal Key
                                    </Button>
                                )}
                            </div>
                        </Card>
                    </div>

                    <Card title="Test AI Connection" className="mt-4">
                        <p className="mb-4 text-sm leading-6 text-dark-300">
                            The test sends a short prompt to the saved provider. It contains no
                            market data and does not run an analysis or change trading settings.
                        </p>
                        <Button
                            variant="secondary"
                            icon={Activity}
                            loading={test.isPending}
                            disabled={
                                !data?.configured ||
                                selectedProvider !== data?.provider ||
                                Boolean(apiKey.trim())
                            }
                            onClick={() => {
                                setFeedback(null);
                                test.mutate();
                            }}
                        >
                            Test Saved Connection
                        </Button>
                    </Card>
                </>
            )}
        </PageWrapper>
    );
}
