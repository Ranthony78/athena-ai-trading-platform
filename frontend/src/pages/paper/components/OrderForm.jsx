import { useState } from "react";
import { Input, Select, Button } from "../../../components/common";
import { INDICES } from "../../../utils/constants";

export default function OrderForm({ onSubmit, loading }) {
    const [form, setForm] = useState({
        symbol: "NIFTY",
        transaction_type: "BUY",
        quantity: 1,
        order_type: "MARKET",
        price: 0,
        product: "MIS",
        tag: "",
    });

    const set = (key, val) => setForm((f) => ({ ...f, [key]: val }));

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <Select
                    label="Symbol"
                    options={INDICES.map((i) => ({ value: i, label: i }))}
                    value={form.symbol}
                    onChange={(e) => set("symbol", e.target.value)}
                />
                <Select
                    label="Type"
                    options={[
                        { value: "BUY", label: "Buy" },
                        { value: "SELL", label: "Sell" },
                    ]}
                    value={form.transaction_type}
                    onChange={(e) => set("transaction_type", e.target.value)}
                />
                <Input
                    label="Quantity"
                    type="number"
                    min="1"
                    value={form.quantity}
                    onChange={(e) => set("quantity", parseInt(e.target.value))}
                />
                <Select
                    label="Order Type"
                    options={[
                        { value: "MARKET", label: "Market" },
                        { value: "LIMIT", label: "Limit" },
                    ]}
                    value={form.order_type}
                    onChange={(e) => set("order_type", e.target.value)}
                />
                {form.order_type === "LIMIT" && (
                    <Input
                        label="Limit Price"
                        type="number"
                        value={form.price}
                        onChange={(e) => set("price", parseFloat(e.target.value))}
                        className="col-span-2"
                    />
                )}
                <Select
                    label="Product"
                    options={[
                        { value: "MIS", label: "MIS (Intraday)" },
                        { value: "NRML", label: "NRML" },
                    ]}
                    value={form.product}
                    onChange={(e) => set("product", e.target.value)}
                />
                <Input
                    label="Tag (optional)"
                    placeholder="strategy name..."
                    value={form.tag}
                    onChange={(e) => set("tag", e.target.value)}
                />
            </div>
            <div className="flex justify-end">
                <Button
                    variant={form.transaction_type === "BUY" ? "success" : "danger"}
                    loading={loading}
                    onClick={() => onSubmit(form)}
                >
                    {form.transaction_type === "BUY" ? "Buy" : "Sell"} {form.symbol}
                </Button>
            </div>
        </div>
    );
}