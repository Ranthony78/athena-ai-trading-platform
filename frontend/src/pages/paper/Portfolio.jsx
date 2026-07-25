import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Spinner } from "../../components/common";
import PortfolioStats from "./components/PortfolioStats";
import { paperAPI } from "../../api/paper";

export default function Portfolio() {
    const queryClient = useQueryClient();

    const { data: portfolio, isLoading } = useQuery({
        queryKey: ["portfolio"],
        queryFn: () => paperAPI.getPortfolio(),
        refetchInterval: 30000,
        select: (res) => res.data.data,
    });

    const { mutate: reset, isPending } = useMutation({
        mutationFn: () => paperAPI.resetPortfolio(),
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
    });

    const links = [
        { href: "/paper/orders", label: "Orders" },
        { href: "/paper/positions", label: "Positions" },
        { href: "/paper/trades", label: "Trade History" },
    ];

    return (
        <PageWrapper
            title="Paper Trading"
            subtitle="Virtual trading portfolio"
            actions={
                <Button
                    variant="danger"
                    size="sm"
                    icon={RefreshCw}
                    loading={isPending}
                    onClick={() => {
                        if (confirm("Reset all paper trading data?")) reset();
                    }}
                >
                    Reset
                </Button>
            }
        >
            {isLoading ? (
                <Spinner text="Loading portfolio..." />
            ) : (
                <>
                    <PortfolioStats portfolio={portfolio} />

                    <div className="grid grid-cols-3 gap-4">
                        {links.map((link) => (
                            <a key={link.href} href={link.href}>
                                <Card className="hover:border-primary-500 cursor-pointer
                                 transition-colors text-center">
                                    <p className="text-sm font-medium text-primary-400">
                                        {link.label} →
                                    </p>
                                </Card>
                            </a>
                        ))}
                    </div>
                </>
            )}
        </PageWrapper>
    );
}