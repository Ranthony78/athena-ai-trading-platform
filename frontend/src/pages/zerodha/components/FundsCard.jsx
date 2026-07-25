import { Card } from "../../../components/common";
import { formatCurrency } from "../../../utils/formatters";

export default function FundsCard({ funds }) {
    if (!funds) return null;

    const equity = funds?.equity || {};

    const items = [
        { label: "Available Cash", value: equity.available?.cash },
        { label: "Available Margin", value: equity.available?.intraday_payin },
        { label: "Used Margin", value: equity.utilised?.debits },
        { label: "Net", value: equity.net },
    ];

    return (
        <Card title="Funds & Margins">
            <div className="space-y-3">
                {items.map((item) => (
                    <div key={item.label}
                        className="flex items-center justify-between py-2
                       border-b border-dark-800 last:border-0">
                        <span className="text-sm text-dark-400">{item.label}</span>
                        <span className="text-sm font-mono font-semibold text-dark-100">
                            {item.value !== undefined
                                ? formatCurrency(item.value)
                                : "—"}
                        </span>
                    </div>
                ))}
            </div>
        </Card>
    );
}