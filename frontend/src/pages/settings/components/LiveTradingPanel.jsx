import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import { Alert, Badge, Button, Card, Input } from "../../../components/common";
import { zerodhaAPI } from "../../../api/zerodha";

function messageOf(error) {
    return (
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        "Something went wrong. Please try again."
    );
}

function untilText(iso) {
    if (!iso) return "";
    return new Date(iso).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Kolkata",
    });
}

// Live-order permission. Hidden until the user has a working Zerodha
// connection. Real orders also need the market to be open and a per-order
// confirmation; this panel only controls the permission layers before that.
export default function LiveTradingPanel() {
    const queryClient = useQueryClient();
    const [phrase, setPhrase] = useState("");
    const [acknowledged, setAcknowledged] = useState(false);
    const [confirmingMaster, setConfirmingMaster] = useState(false);

    const { data: broker } = useQuery({
        queryKey: ["zerodha-status"],
        queryFn: () => zerodhaAPI.getStatus(),
        select: (res) => res.data.data,
    });
    const connected = Boolean(broker?.is_connected && broker?.is_token_valid);

    const { data: state } = useQuery({
        queryKey: ["live-trading"],
        queryFn: () => zerodhaAPI.getLiveTrading(),
        select: (res) => res.data.data,
        enabled: connected,
    });

    const refresh = () => {
        queryClient.invalidateQueries({ queryKey: ["live-trading"] });
        queryClient.invalidateQueries({ queryKey: ["zerodha-status"] });
    };

    const arm = useMutation({
        mutationFn: () => zerodhaAPI.armLiveTrading(phrase),
        onSuccess: () => {
            setPhrase("");
            setAcknowledged(false);
            refresh();
        },
    });
    const disarm = useMutation({
        mutationFn: () => zerodhaAPI.disarmLiveTrading(),
        onSuccess: refresh,
    });
    const master = useMutation({
        mutationFn: (enabled) => zerodhaAPI.setLiveTradingMaster(enabled),
        onSuccess: () => {
            setConfirmingMaster(false);
            refresh();
        },
    });

    if (!connected || !state) return null;

    const phraseMatches = phrase.trim() === state.confirm_phrase;

    return (
        <Card
            title="Live orders"
            subtitle="Permission to send real orders to your Zerodha account"
            actions={
                state.armed ? (
                    <Badge variant="red">Armed until {untilText(state.armed_until)} IST</Badge>
                ) : (
                    <Badge variant="green">Off</Badge>
                )
            }
        >
            <div className="space-y-4">
                {state.locked && (
                    <Alert
                        type="error"
                        title="Locked by the server"
                        message="Live orders are switched off for everyone by a server setting. Only the server administrator can change this."
                    />
                )}

                {state.is_admin && !state.locked && (
                    <div className="rounded-lg border border-dark-700 p-3">
                        <p className="text-sm font-medium text-dark-100">
                            Administrator: allow live orders on this installation
                        </p>
                        <p className="mt-1 text-xs text-dark-400">
                            Currently <strong>{state.master_enabled ? "on" : "off"}</strong>.
                            Turning it off also cancels everyone&apos;s arming immediately.
                        </p>
                        {master.isError && (
                            <p className="mt-2 text-xs text-red-400">{messageOf(master.error)}</p>
                        )}
                        <div className="mt-3 flex flex-wrap items-center gap-2">
                            {state.master_enabled ? (
                                <Button
                                    variant="danger"
                                    size="sm"
                                    loading={master.isPending}
                                    onClick={() => master.mutate(false)}
                                >
                                    Turn off for everyone
                                </Button>
                            ) : confirmingMaster ? (
                                <>
                                    <span className="text-xs text-amber-300">
                                        This lets users on this installation arm real orders.
                                    </span>
                                    <Button
                                        size="sm"
                                        loading={master.isPending}
                                        onClick={() => master.mutate(true)}
                                    >
                                        Yes, allow it
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setConfirmingMaster(false)}
                                    >
                                        Cancel
                                    </Button>
                                </>
                            ) : (
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => setConfirmingMaster(true)}
                                >
                                    Allow live orders…
                                </Button>
                            )}
                        </div>
                    </div>
                )}

                {state.armed ? (
                    <div className="space-y-2">
                        <Alert
                            type="warning"
                            title="Live orders are armed"
                            message={`You can send real orders until ${untilText(state.armed_until)} IST today. Each order still needs market hours and its own confirmation.`}
                        />
                        <Button
                            variant="secondary"
                            icon={ShieldCheck}
                            loading={disarm.isPending}
                            onClick={() => disarm.mutate()}
                        >
                            Disarm now
                        </Button>
                    </div>
                ) : !state.master_enabled || state.locked ? (
                    <p className="text-sm text-dark-400">
                        {state.locked
                            ? ""
                            : "Live orders are not enabled on this installation. An administrator can turn them on."}
                    </p>
                ) : (
                    <div className="space-y-3">
                        <div className="rounded-lg border border-red-500/30 bg-red-950/20 p-3">
                            <p className="flex items-center gap-2 text-sm font-semibold text-red-300">
                                <ShieldAlert className="h-4 w-4" />
                                Read this before you arm
                            </p>
                            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-dark-200">
                                {state.disclaimer.lines.map((line) => (
                                    <li key={line}>{line}</li>
                                ))}
                            </ul>
                        </div>
                        <label className="flex items-start gap-2 text-sm text-dark-200">
                            <input
                                type="checkbox"
                                className="mt-1"
                                checked={acknowledged}
                                onChange={(event) => setAcknowledged(event.target.checked)}
                            />
                            I have read the notice above.
                        </label>
                        <Input
                            label={`Type ${state.confirm_phrase} to arm`}
                            value={phrase}
                            onChange={(event) => setPhrase(event.target.value)}
                            autoComplete="off"
                        />
                        {!state.can_arm && (
                            <p className="text-xs text-amber-300">{state.arm_blocked_reason}</p>
                        )}
                        {arm.isError && (
                            <p className="text-xs text-red-400">{messageOf(arm.error)}</p>
                        )}
                        <Button
                            variant="danger"
                            icon={ShieldAlert}
                            loading={arm.isPending}
                            disabled={!acknowledged || !phraseMatches || !state.can_arm}
                            onClick={() => arm.mutate()}
                        >
                            Arm live orders for today
                        </Button>
                    </div>
                )}
            </div>
        </Card>
    );
}
