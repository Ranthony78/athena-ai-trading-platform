import { useState } from "react";
import { Input, Select, Button } from "../../../components/common";
import { INDICES } from "../../../utils/constants";

export default function AlertForm({ onSubmit, loading }) {
    const [form, setForm] = useState({
        symbol: "NIFTY",
        alert_type: "PRICE_ABOVE",
        target_value: 0,
        message: "",
        notify_email: true,
        notify_telegram: false,
        repeat: false,
    });

    const set = (key, val) => setForm((f) => ({ ...f, [key]: val }));

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <Select label="Symbol"
                    options={INDICES.map((i) => ({ value: i, label: i }))}
                    value={form.symbol}
                    onChange={(e) => set("symbol", e.target.value)}
                />
                <Select label="Alert Type"
                    options={[
                        { value: "PRICE_ABOVE", label: "Price Above" },
                        { value: "PRICE_BELOW", label: "Price Below" },
                        { value: "PRICE_CROSS", label: "Price Cross" },
                    ]}
                    value={form.alert_type}
                    onChange={(e) => set("alert_type", e.target.value)}
                />
            </div>
            <Input label="Target Price" type="number" value={form.target_value}
                onChange={(e) => set("target_value", parseFloat(e.target.value))}
            />
            <Input label="Custom Message (optional)" value={form.message}
                placeholder="Alert message..."
                onChange={(e) => set("message", e.target.value)}
            />
            <div className="flex gap-4">
                {[
                    { key: "notify_email", label: "Email" },
                    { key: "notify_telegram", label: "Telegram" },
                    { key: "repeat", label: "Repeat" },
                ].map(({ key, label }) => (
                    <label key={key} className="flex items-center gap-2 text-sm text-dark-300">
                        <input type="checkbox" checked={form[key]}
                            onChange={(e) => set(key, e.target.checked)} />
                        {label}
                    </label>
                ))}
            </div>
            <Button variant="primary" loading={loading}
                onClick={() => onSubmit(form)} className="w-full">
                Create Alert
            </Button>
        </div>
    );
}