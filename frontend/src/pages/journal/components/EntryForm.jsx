import { useState } from "react";
import { Input, Select, Button } from "../../../components/common";

const MOODS = [
    { value: "CONFIDENT", label: "Confident" },
    { value: "NEUTRAL", label: "Neutral" },
    { value: "ANXIOUS", label: "Anxious" },
    { value: "DISCIPLINED", label: "Disciplined" },
];

const BIASES = [
    { value: "BULLISH", label: "Bullish" },
    { value: "BEARISH", label: "Bearish" },
    { value: "NEUTRAL", label: "Neutral" },
];

export default function EntryForm({ onSubmit, loading }) {
    const [form, setForm] = useState({
        title: "",
        session: "EOD",
        market_bias: "NEUTRAL",
        mood: "NEUTRAL",
        market_notes: "",
        what_worked: "",
        what_didnt_work: "",
        lessons_learned: "",
        tomorrow_plan: "",
        trades_taken: 0,
        winners: 0,
        losers: 0,
        total_pnl: 0,
        rating: 5,
    });

    const set = (key, val) => setForm((f) => ({ ...f, [key]: val }));

    const textarea = (label, key, placeholder = "") => (
        <div>
            <label className="label">{label}</label>
            <textarea
                className="input h-16 resize-none"
                placeholder={placeholder}
                value={form[key]}
                onChange={(e) => set(key, e.target.value)}
            />
        </div>
    );

    return (
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
            <Input
                label="Title"
                placeholder="Today's journal entry..."
                value={form.title}
                onChange={(e) => set("title", e.target.value)}
            />
            <div className="grid grid-cols-2 gap-4">
                <Select label="Market Bias" options={BIASES}
                    value={form.market_bias}
                    onChange={(e) => set("market_bias", e.target.value)}
                />
                <Select label="Mood" options={MOODS}
                    value={form.mood}
                    onChange={(e) => set("mood", e.target.value)}
                />
            </div>
            <div className="grid grid-cols-3 gap-4">
                <Input label="Trades" type="number" value={form.trades_taken}
                    onChange={(e) => set("trades_taken", parseInt(e.target.value))}
                />
                <Input label="Winners" type="number" value={form.winners}
                    onChange={(e) => set("winners", parseInt(e.target.value))}
                />
                <Input label="Losers" type="number" value={form.losers}
                    onChange={(e) => set("losers", parseInt(e.target.value))}
                />
            </div>
            <div className="grid grid-cols-2 gap-4">
                <Input label="Total PnL" type="number" value={form.total_pnl}
                    onChange={(e) => set("total_pnl", parseFloat(e.target.value))}
                />
                <Input label="Rating (1-10)" type="number" min="1" max="10"
                    value={form.rating}
                    onChange={(e) => set("rating", parseInt(e.target.value))}
                />
            </div>
            {textarea("Market Notes", "market_notes", "Market structure observations...")}
            {textarea("What Worked", "what_worked", "What went well today...")}
            {textarea("What Didn't Work", "what_didnt_work", "What went wrong...")}
            {textarea("Lessons Learned", "lessons_learned", "Key takeaways...")}
            {textarea("Tomorrow's Plan", "tomorrow_plan", "Plan for tomorrow...")}
            <div className="flex justify-end pt-2">
                <Button variant="primary" loading={loading} onClick={() => onSubmit(form)}>
                    Save Entry
                </Button>
            </div>
        </div>
    );
}