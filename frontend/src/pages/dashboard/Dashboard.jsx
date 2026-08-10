import { useQuery } from "@tanstack/react-query";
import { PageWrapper, } from "../../components/layout";
import { Card, Spinner } from "../../components/common";
import MarketSummaryCard from "./components/MarketSummaryCard";
import AISignalCard from "./components/AISignalCard";
import PortfolioCard from "./components/PortfolioCard";
import RecentSignalsTable from "./components/RecentSignalsTable";
import { marketAPI } from "../../api/market";
import { analysisAPI } from "../../api/analysis";
import { paperAPI } from "../../api/paper";
import { strategiesAPI } from "../../api/strategies";
import { useSession } from "../../hooks/useMarket";

// Nifty 50 / Bank Nifty are what Athena actually trades — show them first,
// everything else (Sensex, Finnifty, Midcpnifty) is reference context.
const PRIMARY_ORDER = ["NIFTY", "NIFTY50", "BANKNIFTY"];

function sortQuotes(quotes = []) {
    return [...quotes].sort((a, b) => {
        const aIdx = PRIMARY_ORDER.indexOf(a.symbol?.toUpperCase());
        const bIdx = PRIMARY_ORDER.indexOf(b.symbol?.toUpperCase());
        if (aIdx === -1 && bIdx === -1) return 0;
        if (aIdx === -1) return 1;
        if (bIdx === -1) return -1;
        return aIdx - bIdx;
    });
}

export default function Dashboard() {
    const { data: session } = useSession();

    const {
        data: quotes,
        isLoading: quotesLoading,
        dataUpdatedAt,
    } = useQuery({
        queryKey: ["quotes"],
        queryFn: () => marketAPI.getQuotes(),
        refetchInterval: 5000,
        select: (res) => res.data.data,
    });

    const { data: aiSignals } = useQuery({
        queryKey: ["ai-signals"],
        queryFn: () => analysisAPI.getSignals(),
        refetchInterval: 60000,
        select: (res) => res.data.data,
    });

    const { data: portfolio } = useQuery({
        queryKey: ["portfolio"],
        queryFn: () => paperAPI.getPortfolio(),
        refetchInterval: 30000,
        select: (res) => res.data.data,
    });

    const { data: signals } = useQuery({
        queryKey: ["strategy-signals"],
        queryFn: () => strategiesAPI.getSignals({ active: 1 }),
        refetchInterval: 30000,
        select: (res) => res.data.data,
    });

    const isMarketOpen = session?.session === "LIVE";
    const sortedQuotes = sortQuotes(quotes);

    return (
        <PageWrapper
            title="Dashboard"
            subtitle={`Market is ${session?.session || "loading..."}`}
        >
            {/* Top Stats */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    {isMarketOpen && (
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full
                rounded-full bg-green-400 opacity-75" />
                            <span className="relative inline-flex rounded-full h-2 w-2
                bg-green-400" />
                        </span>
                    )}
                    <span className="text-xs text-dark-500">
                        {isMarketOpen && dataUpdatedAt
                            ? `Live — updated ${new Date(dataUpdatedAt).toLocaleTimeString()}`
                            : "Quotes update when market is open"}
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {quotesLoading ? (
                    <div className="col-span-4"><Spinner /></div>
                ) : (
                    sortedQuotes?.map((quote) => (
                        <MarketSummaryCard key={quote.symbol} quote={quote} />
                    ))
                )}
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* AI Signal */}
                <div className="lg:col-span-2">
                    <AISignalCard signals={aiSignals || []} />
                </div>

                {/* Portfolio */}
                <div>
                    <PortfolioCard portfolio={portfolio} />
                </div>
            </div>

            {/* Recent Signals */}
            <RecentSignalsTable signals={signals || []} />
        </PageWrapper>
    );
}