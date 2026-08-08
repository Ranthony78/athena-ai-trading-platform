import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link2, LogOut, ExternalLink } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Input, Spinner, Alert, Badge } from "../../components/common";
import ConnectionStatus from "./components/ConnectionStatus";
import FundsCard from "./components/FundsCard";
import { zerodhaAPI } from "../../api/zerodha";

export default function ZerodhaConnect() {
    const queryClient = useQueryClient();
    const [config, setConfig] = useState({ api_key: "", api_secret: "" });
    const [requestToken, setRequestToken] = useState("");

    const { data: status, isLoading } = useQuery({
        queryKey: ["zerodha-status"],
        queryFn: () => zerodhaAPI.getStatus(),
        select: (res) => res.data.data,
    });

    const { data: loginUrl } = useQuery({
        queryKey: ["zerodha-login-url"],
        queryFn: () => zerodhaAPI.getLoginUrl(),
        select: (res) => res.data.data?.login_url,
        enabled: !status?.is_connected,
    });

    const { data: funds } = useQuery({
        queryKey: ["zerodha-funds"],
        queryFn: () => zerodhaAPI.getFunds(),
        select: (res) => res.data.data,
        enabled: status?.is_connected,
    });

    const { mutate: saveConfig, isPending: saving } = useMutation({
        mutationFn: (data) => zerodhaAPI.saveConfig(data),
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["zerodha-status"] }),
    });

    const { mutate: exchangeToken, isPending: exchanging } = useMutation({
        mutationFn: (token) => zerodhaAPI.exchangeToken(token),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["zerodha-status"] });
            setRequestToken("");
        },
    });

    const { mutate: logout } = useMutation({
        mutationFn: () => zerodhaAPI.logout(),
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["zerodha-status"] }),
    });

    if (isLoading) return <Spinner />;

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
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Status */}
                <ConnectionStatus status={status} />

                {/* Funds */}
                {status?.is_connected && <FundsCard funds={funds} />}
            </div>

            {!status?.is_connected && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Step 1 */}
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

                    {/* Step 2 */}
                    <Card title="Step 2 — Login to Zerodha">
                        <div className="space-y-4">
                            {loginUrl ? (
                                <>
                                    <a href={loginUrl} target="_blank" rel="noreferrer">
                                        <Button variant="primary" icon={ExternalLink} className="w-full">
                                            Login to Zerodha
                                        </Button>
                                    </a>
                                    <Alert type="info"
                                        message="After login, copy the request_token from the redirect URL" />
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
                            ) : (
                                <Alert type="warning" message="Save API credentials first" />
                            )}
                        </div>
                    </Card>
                </div>
            )}

            {/* Quick Links */}
            {status?.is_connected && (
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