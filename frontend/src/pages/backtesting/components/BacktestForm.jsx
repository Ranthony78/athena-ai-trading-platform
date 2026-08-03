import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Input, Select, Button } from "../../../components/common";
import { strategiesAPI } from "../../../api/strategies";
import { INDICES, TIMEFRAMES } from "../../../utils/constants";

export default function BacktestForm({ onSubmit, loading }) {
    const [form, setForm] = useState({
        strategy_id: "",
        symbol: "NIFTY",
        timeframe: "15m",
        from_date: "2024-01-01",
        to_date: "2024-03-31",
        initial_capital: 100000,
        position_size_pct: 10,
        brokerage_per_trade: 20,
    });

    const set = (key, val) => setForm((f) => ({ ...f, [key]: val }));

    const { data: strategies } = useQuery({
        queryKey: ["strategies"],
        queryFn: () => strategiesAPI.getStrategies(),
        select: (res) => res.data.data?.map((s) => ({
            value: s.id, label: s.name,
        })) || [],
    });

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <Select label="Strategy" options={strategies || []}
                    value={form.strategy_id}
                    onChange={(e) => set("strategy_id", parseInt(e.target.value))}
                />
                <Select label="Symbol"
                    options={INDICES.map((i) => ({ value: i, label: i }))}
                    value={form.symbol}
                    onChange={(e) => set("symbol", e.target.value)}
                />
                <Select label="Timeframe" options={TIMEFRAMES}
                    value={form.timeframe}
                    onChange={(e) => set("timeframe", e.target.value)}
                />
                <Input label="Initial Capital" type="number"
                    value={form.initial_capital}
                    onChange={(e) => set("initial_capital", parseFloat(e.target.value))}
                />
                <Input label="From Date" type="date" value={form.from_date}
                    onChange={(e) => set("from_date", e.target.value)}
                />
                <Input label="To Date" type="date" value={form.to_date}
                    onChange={(e) => set("to_date", e.target.value)}
                />
                <Input label="Position Size %" type="number"
                    value={form.position_size_pct}
                    onChange={(e) => set("position_size_pct", parseFloat(e.target.value))}
                />
                <Input label="Brokerage per Trade" type="number"
                    value={form.brokerage_per_trade}
                    onChange={(e) => set("brokerage_per_trade", parseFloat(e.target.value))}
                />
            </div>
            <Button variant="primary" loading={loading}
                onClick={() => onSubmit(form)} className="w-full">
                {loading ? "Running Backtest..." : "Run Backtest"}
            </Button>
        </div>
    );
}