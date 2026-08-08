import { useQuery } from "@tanstack/react-query";
import { marketAPI } from "../api/market";
import useMarketStore from "../store/marketStore";
import { useEffect } from "react";

export function useSession() {
    const { setSession } = useMarketStore();

    const query = useQuery({
        queryKey: ["session"],
        queryFn: () => marketAPI.getSession(),
        refetchInterval: 60000,
        select: (res) => res.data.data,
    });

    useEffect(() => {
        if (query.data) setSession(query.data);
    }, [query.data]);

    return query;
}

export function useQuotes() {
    return useQuery({
        queryKey: ["quotes"],
        queryFn: () => marketAPI.getQuotes(),
        refetchInterval: 5000,
        select: (res) => res.data.data,
    });
}

export function useQuote(symbol) {
    return useQuery({
        queryKey: ["quote", symbol],
        queryFn: () => marketAPI.getQuote(symbol),
        refetchInterval: 5000,
        select: (res) => res.data.data,
        enabled: !!symbol,
    });
}

export function useIndices() {
    return useQuery({
        queryKey: ["indices"],
        queryFn: () => marketAPI.getIndices(),
        refetchInterval: 10000,
        select: (res) => res.data.data,
    });
}

export function useHistorical(symbol, timeframe, limit = 100) {
    return useQuery({
        queryKey: ["historical", symbol, timeframe, limit],
        queryFn: () =>
            marketAPI.getHistorical(symbol, { timeframe, limit }),
        select: (res) => res.data.data,
        enabled: !!symbol && !!timeframe,
    });
}