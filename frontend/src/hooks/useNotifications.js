import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notificationsAPI } from "../api/notifications";
import useNotificationStore from "../store/notificationStore";
import { useEffect } from "react";

export function useNotifications(params = {}) {
    const { setNotifications, setUnreadCount } = useNotificationStore();

    const query = useQuery({
        queryKey: ["notifications", params],
        queryFn: () => notificationsAPI.getNotifications(params),
        refetchInterval: 30000,
        select: (res) => res.data.data,
    });

    useEffect(() => {
        if (query.data) {
            setNotifications(query.data.notifications || []);
            setUnreadCount(query.data.unread_count || 0);
        }
    }, [query.data]);

    return query;
}

export function useMarkRead() {
    const queryClient = useQueryClient();
    const { markRead } = useNotificationStore();

    return useMutation({
        mutationFn: (id) => notificationsAPI.markRead(id),
        onSuccess: (_, id) => {
            markRead(id);
            queryClient.invalidateQueries({ queryKey: ["notifications"] });
        },
    });
}

export function useMarkAllRead() {
    const queryClient = useQueryClient();
    const { markAllRead } = useNotificationStore();

    return useMutation({
        mutationFn: () => notificationsAPI.markAllRead(),
        onSuccess: () => {
            markAllRead();
            queryClient.invalidateQueries({ queryKey: ["notifications"] });
        },
    });
}