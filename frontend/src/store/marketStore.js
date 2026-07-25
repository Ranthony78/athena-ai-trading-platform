import { create } from "zustand";

const useMarketStore = create((set, get) => ({
    quotes: {},
    session: null,
    isLive: false,
    selectedSymbol: "NIFTY",
    selectedTimeframe: "15m",

    setQuote: (symbol, quote) =>
        set((state) => ({
            quotes: { ...state.quotes, [symbol]: quote },
        })),

    setQuotes: (quotes) =>
        set({ quotes }),

    setSession: (session) =>
        set({
            session,
            isLive: session?.is_live || false,
        }),

    setSelectedSymbol: (symbol) =>
        set({ selectedSymbol: symbol }),

    setSelectedTimeframe: (timeframe) =>
        set({ selectedTimeframe: timeframe }),

    getQuote: (symbol) =>
        get().quotes[symbol] || null,
}));

export default useMarketStore;