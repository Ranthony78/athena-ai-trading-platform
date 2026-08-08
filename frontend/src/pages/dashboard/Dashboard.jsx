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

export default function Dashboard() {
    const { data: session } = useSession();

    const { data: quotes, isLoading: quotesLoading } = useQuery({
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

    return (
        <PageWrapper
            title="Dashboard"
            subtitle={`Market is ${session?.session || "loading..."}`}
        >
            {/* Top Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {quotesLoading ? (
                    <div className="col-span-4"><Spinner /></div>
                ) : (
                    quotes?.map((quote) => (
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