import { useState } from "react";
import { Input, Select, Button } from "../../../components/common";

const STRATEGY_TYPES = [
    { value: "EMA_CROSSOVER", label: "EMA Crossover" },
    { value: "RSI", label: "RSI" },
    { value: "VWAP", label: "VWAP" },
    { value: "ORB", label: "Opening Range Breakout" },
];

const TIMEFRAMES = [
    { value: "1m", label: "1 Min" },
    { value: "5m", label: "5 Min" },
    { value: "15m", label: "15 Min" },
    { value: "30m", label: "30 Min" },
    { value: "1h", label: "1 Hour" },
    { value: "1d", label: "1 Day" },
];

export default function StrategyForm({ onSubmit, loading }) {
    const [form, setForm] = useState({
        name: "",
        description: "",
        strategy_type: "EMA_CROSSOVER",
        timeframe: "15m",
        is_enabled: true,
        parameters: {},
    });

    const set = (key, val) => setForm((f) => ({ ...f, [key]: val }));

    return (
        <div className="space-y-4">
            <Input
                label="Strategy Name"
                placeholder="My EMA Strategy"
                value={form.name}
                onChange={(e) => set("name", e.target.value)}
            />
            <Select
                label="Strategy Type"
                options={STRATEGY_TYPES}
                value={form.strategy_type}
                onChange={(e) => set("strategy_type", e.target.value)}
            />
            <Select
                label="Timeframe"
                options={TIMEFRAMES}
                value={form.timeframe}
                onChange={(e) => set("timeframe", e.target.value)}
            />
            <div>
                <label className="label">Description</label>
                <textarea
                    className="input h-20 resize-none"
                    placeholder="Optional description..."
                    value={form.description}
                    onChange={(e) => set("description", e.target.value)}
                />
            </div>
            <div className="flex justify-end gap-2">
                <Button
                    variant="primary"
                    loading={loading}
                    onClick={() => onSubmit(form)}
                >
                    Create Strategy
                </Button>
            </div>
        </div>
    );
}