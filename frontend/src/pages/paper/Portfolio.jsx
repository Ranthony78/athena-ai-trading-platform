import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, AlertTriangle } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Spinner, Modal } from "../../components/common";
import PortfolioStats from "./components/PortfolioStats";
import { paperAPI } from "../../api/paper";

export default function Portfolio() {
    const queryClient = useQueryClient();
    const [showResetConfirm, setShowResetConfirm] = useState(false);

    const { data: portfolio, isLoading } = useQuery({
        queryKey: ["portfolio"],
        queryFn: () => paperAPI.getPortfolio(),
        refetchInterval: 30000,
        select: (res) => res.data.data,
    });

    const { mutate: reset, isPending } = useMutation({
        mutationFn: () => paperAPI.resetPortfolio(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["portfolio"] });
            setShowResetConfirm(false);
        },
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
                    onClick={() => setShowResetConfirm(true)}
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

            <Modal
                isOpen={showResetConfirm}
                onClose={() => setShowResetConfirm(false)}
                title="Reset paper trading data?"
                size="sm"
            >
                <div className="flex gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                    <p className="text-sm text-dark-300">
                        This will permanently clear your balance, positions,
                        orders, and trade history, and restore your account
                        to its starting ₹10.00 L balance. This cannot be undone.
                    </p>
                </div>

                <div className="flex justify-end gap-2 mt-6">
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setShowResetConfirm(false)}
                        disabled={isPending}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="danger"
                        size="sm"
                        loading={isPending}
                        onClick={() => reset()}
                    >
                        Reset Everything
                    </Button>
                </div>
            </Modal>
        </PageWrapper>
    );
}
