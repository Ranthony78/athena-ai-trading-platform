import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { LogOut, ExternalLink } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Input, Spinner, Alert } from "../../components/common";
import ConnectionStatus from "./components/ConnectionStatus";
import FundsCard from "./components/FundsCard";
import { zerodhaAPI } from "../../api/zerodha";

export default function ZerodhaConnect() {
    const queryClient = useQueryClient();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [config, setConfig] = useState({ api_key: "", api_secret: "" });
    const [requestToken, setRequestToken] = useState("");
    const [showManualEntry, setShowManualEntry] = useState(false);
    const autoExchangeAttempted = useRef(false);

    const { data: status, isLoading } = useQuery({
        queryKey: ["zerodha-status"],
        queryFn: () => zerodhaAPI.getStatus(),
        select: (res) => res.data.data,
    });

    const isActive = Boolean(status?.is_connected && status?.is_token_valid);

    const { data: loginUrl } = useQuery({
        queryKey: ["zerodha-login-url"],
        queryFn: () => zerodhaAPI.getLoginUrl(),
        select: (res) => res.data.data?.login_url,
        enabled: !isActive,
    });

    const { data: funds } = useQuery({
        queryKey: ["zerodha-funds"],
        queryFn: () => zerodhaAPI.getFunds(),
        select: (res) => res.data.data,
        enabled: isActive,
    });

    const { mutate: saveConfig, isPending: saving } = useMutation({
        mutationFn: (data) => zerodhaAPI.saveConfig(data),
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["zerodha-status"] }),
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
                    message={`Automatic login failed: ${exchangeError?.message || "please try reconnecting"}.`} />
            )}

            {!isActive && status?.is_connected && !autoExchangeInFlight && (
                <Alert type="warning"
                    message="Your Zerodha session has expired for today — reconnect below to continue." />
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ConnectionStatus status={status} />
                {isActive && <FundsCard funds={funds} />}
            </div>

            {!isActive && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card title="Step 1 — Save API Credentials">
                        <div className="space-y-4">
                            <Input label="API Key" value={config.api_key}
                                onChange={(e) => setConfig(c => ({ ...c, api_key: e.target.value }))}
                                placeholder="Your Kite API key" />
                            <Input label="API Secret" type="password" value={config.api_secret}
                                onChange={(e) => setConfig(c => ({ ...c, api_secret: e.target.value }))}
                                placeholder="Your Kite API secret" />
                            <Button variant="primary" loading={saving}
                                onClick={() => saveConfig(config)} className="w-full">
                                Save Credentials
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
                                        message="You'll be redirected to Kite, then brought straight back here — no copying required." />

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
                            ) : (
                                <Alert type="warning" message="Save API credentials first" />
                            )}
                        </div>
                    </Card>
                </div>
            )}

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