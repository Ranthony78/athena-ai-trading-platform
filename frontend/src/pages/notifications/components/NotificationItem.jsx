import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notificationsAPI } from "../../../api/notifications";
import { formatRelativeTime } from "../../../utils/formatters";

export default function NotificationItem({ notification }) {
    const queryClient = useQueryClient();

    const { mutate: markRead } = useMutation({
        mutationFn: () => notificationsAPI.markRead(notification.id),
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["notifications"] }),
    });

    const isUnread = notification.status !== "READ";

    return (
        <div
            className={`flex items-start gap-3 p-4 cursor-pointer
        hover:bg-dark-800/50 transition-colors
        ${isUnread ? "bg-primary-900/5" : ""}`}
            onClick={() => isUnread && markRead()}
        >
            {isUnread && (
                <div className="w-2 h-2 rounded-full bg-primary-500 mt-1.5 shrink-0" />
            )}
            <div className={`flex-1 ${!isUnread ? "ml-5" : ""}`}>
                <p className={`text-sm ${isUnread ? "text-dark-100 font-medium" : "text-dark-300"}`}>
                    {notification.title}
                </p>
                <p className="text-xs text-dark-500 mt-0.5">
                    {notification.message}
                </p>
                <p className="text-xs text-dark-600 mt-1">
                    {formatRelativeTime(notification.created_at)}
                </p>
            </div>
        </div>
    );
}