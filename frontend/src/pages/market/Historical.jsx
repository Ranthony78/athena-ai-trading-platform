import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Select, Input, Button, Spinner } from "../../components/common";
import { marketAPI } from "../../api/market";
import { INDICES, TIMEFRAMES } from "../../utils/constants";
import { formatNumber, formatDateTime } from "../../utils/formatters";

export default function Historical() {
    const [symbol, setSymbol] = useState("NIFTY");
    const [timeframe, setTimeframe] = useState("15m");
    const [limit, setLimit] = useState(100);

    const { data: candles, isLoading, refetch } = useQuery({
        queryKey: ["historical", symbol, timeframe, limit],
        queryFn: () => marketAPI.getHistorical(symbol, { timeframe, limit }),
        select: (res) => res.data.data,
        enabled: !!symbol,
    });

    const columns = ["Time", "Open", "High", "Low", "Close", "Volume"];

    return (
        <PageWrapper
            title="Historical Data"
            subtitle="OHLCV candle data"
            actions={
                <div className="flex items-center gap-2">
                    <Select
                        options={INDICES.map((i) => ({ value: i, label: i }))}
                        value={symbol}
                        onChange={(e) => setSymbol(e.target.value)}
                        className="w-36"
                    />
                    <Select
                        options={TIMEFRAMES}
                        value={timeframe}
                        onChange={(e) => setTimeframe(e.target.value)}
                        className="w-28"
                    />
                    <Input
                        type="number"
                        value={limit}
                        onChange={(e) => setLimit(e.target.value)}
                        className="w-24"
                        placeholder="Limit"
                    />
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={() => refetch()}
                    >
                        Load
                    </Button>
                </div>
            }
        >
            <Card padding={false}>
                {isLoading ? (
                    <Spinner text="Loading candles..." />
                ) : (
                    <div className="overflow-x-auto">
                        <table className="table text-xs">
                            <thead>
                                <tr>
                                    {columns.map((col) => (
                                        <th key={col}>{col}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {(candles || []).map((c, i) => (
                                    <tr key={i}>
                                        <td className="font-mono text-dark-400">
                                            {formatDateTime(c.candle_time)}
                                        </td>
                                        <td className="font-mono">{formatNumber(c.open)}</td>
                                        <td className="font-mono text-green-400">
                                            {formatNumber(c.high)}
                                        </td>
                                        <td className="font-mono text-red-400">
                                            {formatNumber(c.low)}
                                        </td>
                                        <td className="font-mono font-semibold">
                                            {formatNumber(c.close)}
                                        </td>
                                        <td className="font-mono text-dark-400">
                                            {c.volume?.toLocaleString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </Card>
        </PageWrapper>
    );
}