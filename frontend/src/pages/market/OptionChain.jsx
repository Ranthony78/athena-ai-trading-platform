import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Select, Spinner, EmptyState } from "../../components/common";
import OptionChainTable from "./components/OptionChainTable";
import { marketAPI } from "../../api/market";
import { INDICES } from "../../utils/constants";

export default function OptionChain() {
    const [symbol, setSymbol] = useState("NIFTY");

    const { data: chain, isLoading } = useQuery({
        queryKey: ["option-chain", symbol],
        queryFn: () => marketAPI.getOptionChain(symbol),
        refetchInterval: 10000,
        select: (res) => res.data.data,
    });

    const { data: expiries } = useQuery({
        queryKey: ["expiry", symbol],
        queryFn: () => marketAPI.getExpiry(symbol),
        select: (res) => res.data.data,
    });

    return (
        <PageWrapper
            title="Option Chain"
            subtitle={`Live option chain for ${symbol}`}
            actions={
                <Select
                    options={INDICES.map((i) => ({ value: i, label: i }))}
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    className="w-40"
                />
            }
        >
            <Card padding={false}>
                {isLoading ? (
                    <Spinner text="Loading option chain..." />
                ) : !chain?.length ? (
                    <EmptyState
                        title="No option chain data"
                        description="Import NFO instruments and connect to live data"
                    />
                ) : (
                    <OptionChainTable chain={chain} />
                )}
            </Card>
        </PageWrapper>
    );
}