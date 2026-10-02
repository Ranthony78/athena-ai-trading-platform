import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { LogOut, ExternalLink, RefreshCw } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Input, Spinner, Alert } from "../../components/common";
import ConnectionStatus from "./components/ConnectionStatus";
import FundsCard from "./components/FundsCard";
import { zerodhaAPI } from "../../api/zerodha";

function formatApiError(error, action) {
    const response = error?.response;

    if (!response) {
        return `No response while ${action}. Check that Athena's backend is running and the /api proxy can reach it.`;
    }

    const status = response.status;
    const serverMessage = response.data?.message;

    if (status === 401) {
        return `Athena rejected the request while ${action} (HTTP 401). Sign in again, then retry.`;
    }
    if (status >= 500) {
        return `${action} failed (HTTP ${status}). Check the Athena backend process and its logs.`;
    }

    return serverMessage
        ? `${action} failed (HTTP ${status}): ${serverMessage}`
        : `${action} failed (HTTP ${status}).`;
}

function formatCredentialSaveError(error) {
    const response = error?.response;
    const errors = response?.data?.errors;
    const allowedFields = ["api_key", "api_secret", "mcp_url"];
    const invalidFields = allowedFields.filter((field) =>
        Object.prototype.hasOwnProperty.call(errors || {}, field)
    );
    const summary = formatApiError(error, "Saving Zerodha credentials");
    return invalidFields.length
        ? `${summary} Invalid fields: ${invalidFields.join(", ")}.`
        : summary;
}

export default function ZerodhaConnect() {
    const queryClient = useQueryClient();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [config, setConfig] = useState({ api_key: "", api_secret: "" });
    const [configHydrated, setConfigHydrated] = useState(false);
    const [saveFeedback, setSaveFeedback] = useState(null);
    const [requestToken, setRequestToken] = useState("");
    const [showManualEntry, setShowManualEntry] = useState(false);
    const autoExchangeAttempted = useRef(false);

    const { data: status, isLoading } = useQuery({
        queryKey: ["zerodha-status"],
        queryFn: () => zerodhaAPI.getStatus(),
        select: (res) => res.data.data,
    });

    // The API secret is intentionally excluded by the backend serializer.
    // Loading the public API key lets a saved account reconnect after refresh.
    const {
        data: savedConfig,
        isLoading: loadingConfig,
        isFetching: fetchingConfig,
        isError: configLoadFailed,
        error: configLoadError,
        refetch: refetchConfig,
    } = useQuery({
        queryKey: ["zerodha-config"],
        queryFn: () => zerodhaAPI.getConfig(),
        select: (res) => res.data.data,
    });

    useEffect(() => {
        if (!configHydrated && savedConfig) {
            setConfig((current) => ({
                ...current,
                api_key: current.api_key || savedConfig.api_key || "",
            }));
            setConfigHydrated(true);
        }
    }, [configHydrated, savedConfig]);

    const isActive = Boolean(status?.is_connected && status?.is_token_valid);
    const liveOrderPermission = typeof status?.live_orders_enabled === "boolean"
        ? (status.live_orders_enabled ? "enabled" : "disabled")
        : "unknown";

    const {
        data: loginUrl,
        isFetching: loadingLoginUrl,
        isError: loginUrlFailed,
        error: loginUrlError,
        refetch: refetchLoginUrl,
    } = useQuery({
        queryKey: ["zerodha-login-url"],
        queryFn: () => zerodhaAPI.getLoginUrl(),
        select: (res) => res.data.data?.login_url,
        enabled: !isActive && Boolean(savedConfig?.api_key),
    });

    const { data: funds } = useQuery({
        queryKey: ["zerodha-funds"],
        queryFn: () => zerodhaAPI.getFunds(),
        select: (res) => res.data.data,
        enabled: isActive,
    });

    const { mutate: saveConfig, isPending: saving } = useMutation({
        mutationFn: (data) => zerodhaAPI.saveConfig(data),
        onSuccess: async (res) => {
            const saved = res.data.data;
            if (saved) {
                // Keep the raw Axios response shape used by the query's select.
                queryClient.setQueryData(["zerodha-config"], res);
            }
            setConfig((current) => ({ ...current, api_secret: "" }));
            setSaveFeedback({
                type: "success",
                message: "Credentials saved. Refreshing your Kite login link…",
            });
            await Promise.all([
                queryClient.invalidateQueries({ queryKey: ["zerodha-status"] }),
                queryClient.invalidateQueries({ queryKey: ["zerodha-config"] }),
                queryClient.invalidateQueries({ queryKey: ["zerodha-login-url"] }),
            ]);
        },
        onError: (error) => {
            setSaveFeedback({
                type: "error",
                message: formatCredentialSaveError(error),
            });
        },
    });

    const {
        mutate: exchangeToken,
        isPending: exchanging,
        isError: exchangeFailed,
        error: exchangeError,
    } = useMutation({
        mutationFn: (token) => zerodhaAPI.exchangeToken(token),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["zerodha-status"] });
            setRequestToken("");
            navigate("/zerodha", { replace: true });
        },
    });

    const { mutate: logout } = useMutation({
        mutationFn: () => zerodhaAPI.logout(),
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["zerodha-status"] }),
    });

    useEffect(() => {
        const requestTokenParam = searchParams.get("request_token");
        const statusParam = searchParams.get("status");

        if (autoExchangeAttempted.current) return;

        if (statusParam === "success" && requestTokenParam) {
            autoExchangeAttempted.current = true;
            exchangeToken(requestTokenParam);
        } else if (statusParam && statusParam !== "success") {
            autoExchangeAttempted.current = true;
            navigate("/zerodha", { replace: true });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchParams]);

    if (isLoading) return <Spinner />;

    const autoExchangeInFlight =
        exchanging && Boolean(searchParams.get("request_token"));

    return (
        <PageWrapper
            title="Zerodha Connection"
            subtitle="Connect your Kite account"
            actions={
                status?.is_connected && (
                    <Button variant="danger" size="sm" icon={LogOut}
                        onClick={() => logout()}>
                        Disconnect
                    </Button>
                )
            }
        >
            {autoExchangeInFlight && (
                <Alert type="info" message="Completing Zerodha login..." />
            )}

            {exchangeFailed && !autoExchangeInFlight && (
                <Alert type="error"
                    message={`Automatic login failed: ${exchangeError?.response?.data?.message || exchangeError?.message || "please try reconnecting"}.`} />
            )}

            {!isActive && status?.is_connected && !autoExchangeInFlight && (
                <Alert type="warning"
                    message="Your Zerodha session has expired for today — reconnect below to continue." />
            )}

            {configLoadFailed && (
                <div className="space-y-3">
                    <Alert type="error"
                        message={formatApiError(configLoadError, "Loading saved Zerodha settings")} />
                    <Button variant="secondary" icon={RefreshCw} loading={fetchingConfig}
                        onClick={() => refetchConfig()}>
                        Retry Saved Settings
                    </Button>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ConnectionStatus status={status} />
                {isActive && <FundsCard funds={funds} />}
            </div>

            {!isActive && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card title={`Step 1 — ${savedConfig?.api_key ? "Update" : "Save"} API Credentials`}>
                        <div className="space-y-4">
                            <Input label="API Key" value={config.api_key}
                                onChange={(e) => {
                                    setSaveFeedback(null);
                                    setConfig(c => ({ ...c, api_key: e.target.value }));
                                }}
                                placeholder="Your Kite API key" />
                            <Input label="API Secret" type="password" value={config.api_secret}
                                onChange={(e) => {
                                    setSaveFeedback(null);
                                    setConfig(c => ({ ...c, api_secret: e.target.value }));
                                }}
                                placeholder={savedConfig?.api_key
                                    ? "Enter only when updating your API credentials"
                                    : "Your Kite API secret"} />
                            {savedConfig?.api_key && (
                                <p className="text-xs text-dark-400">
                                    The saved API secret is not displayed here. Leave this field blank unless you are updating credentials.
                                </p>
                            )}
                            {saveFeedback && (
                                <Alert type={saveFeedback.type} message={saveFeedback.message} />
                            )}
                            <Button variant="primary" loading={saving}
                                disabled={!config.api_key.trim() || !config.api_secret.trim()}
                                onClick={() => saveConfig({
                                    api_key: config.api_key.trim(),
                                    api_secret: config.api_secret.trim(),
                                })}
                                className="w-full">
                                {savedConfig?.api_key ? "Update Credentials" : "Save Credentials"}
                            </Button>
                        </div>
                    </Card>

                    <Card title={status?.is_connected ? "Step 2 — Reconnect to Zerodha" : "Step 2 — Login to Zerodha"}>
                        <div className="space-y-4">
                            {loginUrl ? (
                                <>
                                    <a href={loginUrl}>
                                        <Button variant="primary" icon={ExternalLink}
                                            loading={autoExchangeInFlight} className="w-full">
                                            {status?.is_connected ? "Reconnect to Zerodha" : "Login to Zerodha"}
                                        </Button>
                                    </a>
                                    <Alert type="info"
                                        message="After Kite login, you should return here automatically. Set the Kite app redirect URL to this portal's address ending in /zerodha." />

                                    {!showManualEntry ? (
                                        <button
                                            type="button"
                                            className="text-xs text-dark-500 hover:text-dark-300 underline"
                                            onClick={() => setShowManualEntry(true)}
                                        >
                                            Redirect didn't work? Enter request_token manually
                                        </button>
                                    ) : (
                                        <>
                                            <Input label="Request Token"
                                                value={requestToken}
                                                onChange={(e) => setRequestToken(e.target.value)}
                                                placeholder="Paste request_token here" />
                                            <Button variant="success" loading={exchanging}
                                                onClick={() => exchangeToken(requestToken)}
                                                className="w-full" disabled={!requestToken}>
                                                Exchange Token
                                            </Button>
                                        </>
                                    )}
                                </>
                            ) : loginUrlFailed ? (
                                <div className="space-y-3">
                                    <Alert type="error"
                                        message={formatApiError(loginUrlError, "Preparing the Kite login link")} />
                                    <Button variant="secondary" icon={RefreshCw}
                                        loading={loadingLoginUrl}
                                        onClick={() => refetchLoginUrl()} className="w-full">
                                        Retry Login Link
                                    </Button>
                                </div>
                            ) : loadingConfig ? (
                                <Alert type="info" message="Checking for saved Kite credentials…" />
                            ) : savedConfig?.api_key ? (
                                <Alert type="info" message="Preparing your Kite login link…" />
                            ) : (
                                <Alert type="warning"
                                    message="Save your Kite API key and secret to prepare the login link." />
                            )}
                        </div>
                    </Card>
                </div>
            )}

            <Alert type={status?.live_orders_enabled ? "warning" : "info"}
                message={`Server live-order permission is currently ${liveOrderPermission}. Connecting your Kite account does not change this setting.`} />

            {isActive && (
                <div className="grid grid-cols-2 gap-4">
                    {[
                        { href: "/zerodha/orders", label: "Live Orders" },
                        { href: "/zerodha/positions", label: "Live Positions" },
                    ].map((link) => (
                        <a key={link.href} href={link.href}>
                            <Card className="hover:border-primary-500 cursor-pointer
                               transition-colors text-center">
                                <p className="text-sm font-medium text-primary-400">
                                    {link.label} →
                                </p>
                            </Card>
                        </a>
                    ))}
                </div>
            )}
        </PageWrapper>
    );
}
