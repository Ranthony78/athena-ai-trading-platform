import { useState } from "react";
import { Brain } from "lucide-react";
import { Card, Select, Button } from "../../../components/common";
import { INDICES, TIMEFRAMES } from "../../../utils/constants";

const SESSION_TYPES = [
    { value: "MARKET_ANALYSIS", label: "Market Analysis" },
    { value: "SETUP_SCANNER", label: "Setup Scanner" },
    { value: "RISK_ASSESSMENT", label: "Risk Assessment" },
];

export default function AnalysisForm({ onSubmit, loading }) {
    const [form, setForm] = useState({
        symbol: "NIFTY",
        timeframe: "15m",
        session_type: "MARKET_ANALYSIS",
        persist: true,
    });

    const set = (key, val) =>
        setForm((f) => ({ ...f, [key]: val }));

    return (
        <Card title="Analysis Settings">
            <div className="space-y-4">
                <Select
                    label="Symbol"
                    options={INDICES.map((i) => ({ value: i, label: i }))}
                    value={form.symbol}
                    onChange={(e) => set("symbol", e.target.value)}
                />
                <Select
                    label="Timeframe"
                    options={TIMEFRAMES}
                    value={form.timeframe}
                    onChange={(e) => set("timeframe", e.target.value)}
                />
                <Select
                    label="Analysis Type"
                    options={SESSION_TYPES}
                    value={form.session_type}
                    onChange={(e) => set("session_type", e.target.value)}
                />

                <div className="flex items-center gap-2">
                    <input
                        type="checkbox"
                        id="persist"
                        checked={form.persist}
                        onChange={(e) => set("persist", e.target.checked)}
                        className="rounded"
                    />
                    <label htmlFor="persist" className="text-sm text-dark-300">
                        Save to history
                    </label>
                </div>

                <Button
                    variant="primary"
                    icon={Brain}
                    loading={loading}
                    onClick={() => onSubmit(form)}
                    className="w-full"
                >
                    {loading ? "Analyzing..." : "Run Analysis"}
                </Button>
            </div>
        </Card>
    );
}