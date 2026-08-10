import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCheck } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Badge, Spinner, EmptyState } from "../../components/common";
import NotificationItem from "./components/NotificationItem";
import { notificationsAPI } from "../../api/notifications";
import { formatRelativeTime } from "../../utils/formatters";

export default function Notifications() {
    const queryClient = useQueryClient();

    const { data, isLoading } = useQuery({
        queryKey: ["notifications"],
        queryFn: () => notificationsAPI.getNotifications(),
        select: (res) => res.data.data,
    });

    const { mutate: markAllRead } = useMutation({
        mutationFn: () => notificationsAPI.markAllRead(),
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["notifications"] }),
    });

    return (
        <PageWrapper
            title="Notifications"
            subtitle={`${data?.unread_count || 0} unread`}
            actions={
                <div className="flex gap-2">
                    <Button variant="secondary" size="sm" icon={CheckCheck}
                        onClick={() => markAllRead()}>
                        Mark All Read
                    </Button>
                    <a href="/notifications/alerts">
                        <Button variant="secondary" size="sm">Alerts</Button>
                    </a>
                    <a href="/notifications/preferences">
                        <Button variant="secondary" size="sm">Preferences</Button>
                    </a>
                </div>
            }
        >
            <Card padding={false}>
                {isLoading ? <Spinner /> : !data?.notifications?.length ? (
                    <EmptyState title="No notifications" />
                ) : (
                    <div className="divide-y divide-dark-800">
                        {data.notifications.map((n) => (
                            <NotificationItem key={n.id} notification={n} />
                        ))}
                    </div>
                )}
            </Card>
        </PageWrapper>
    );
}