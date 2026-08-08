import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Spinner } from "../../components/common";
import { notificationsAPI } from "../../api/notifications";
import { useState, useEffect } from "react";

export default function Preferences() {
    const queryClient = useQueryClient();
    const [form, setForm] = useState(null);

    const { data: prefs, isLoading } = useQuery({
        queryKey: ["notification-prefs"],
        queryFn: () => notificationsAPI.getPreferences(),
        select: (res) => res.data.data,
    });

    useEffect(() => {
        if (prefs) setForm(prefs);
    }, [prefs]);

    const { mutate: update, isPending } = useMutation({
        mutationFn: (data) => notificationsAPI.updatePreferences(data),
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["notification-prefs"] }),
    });

    if (isLoading) return <Spinner />;
    if (!form) return null;

    const set = (key, val) => setForm((f) => ({ ...f, [key]: val }));

    const toggle = (label, key) => (
        <label className="flex items-center justify-between py-2">
            <span className="text-sm text-dark-200">{label}</span>
            <input type="checkbox" checked={form[key] || false}
                onChange={(e) => set(key, e.target.checked)}
                className="w-4 h-4" />
        </label>
    );

    return (
        <PageWrapper title="Notification Preferences">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card title="Channels">
                    <div className="divide-y divide-dark-800">
                        {toggle("Email Notifications", "email_enabled")}
                        {toggle("Telegram Notifications", "telegram_enabled")}
                    </div>
                    {form.telegram_enabled && (
                        <div className="mt-3">
                            <label className="label">Telegram Chat ID</label>
                            <input className="input" value={form.telegram_chat_id || ""}
                                onChange={(e) => set("telegram_chat_id", e.target.value)} />
                        </div>
                    )}
                </Card>

                <Card title="Events">
                    <div className="divide-y divide-dark-800">
                        {toggle("AI Signals", "notify_ai_signals")}
                        {toggle("Strategy Signals", "notify_strategy_signals")}
                        {toggle("Price Alerts", "notify_price_alerts")}
                        {toggle("Trade Execution", "notify_trade_execution")}
                        {toggle("Daily Summary", "notify_daily_summary")}
                        {toggle("Market Open", "notify_market_open")}
                        {toggle("Market Close", "notify_market_close")}
                    </div>
                </Card>
            </div>

            <Button variant="primary" loading={isPending}
                onClick={() => update(form)}>
                Save Preferences
            </Button>
        </PageWrapper>
    );
}