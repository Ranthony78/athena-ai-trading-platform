import { Bell, LogOut, User, Wifi, WifiOff } from "lucide-react";
import { useLogout } from "../../hooks/useAuth";
import { useSession } from "../../hooks/useMarket";
import useAuthStore from "../../store/authStore";
import useNotificationStore from "../../store/notificationStore";
import { getSessionColor } from "../../utils/helpers";

export default function Topbar() {
    const { user } = useAuthStore();
    const { mutate: logout } = useLogout();
    const { unreadCount } = useNotificationStore();
    const { data: session } = useSession();

    return (
        <header className="h-16 bg-dark-900 border-b border-dark-800
                       flex items-center justify-between px-6 shrink-0">

            {/* Session Status */}
            <div className="flex items-center gap-3">
                {session ? (
                    <div className="flex items-center gap-2">
                        {session.is_live ? (
                            <Wifi className="w-4 h-4 text-green-400" />
                        ) : (
                            <WifiOff className="w-4 h-4 text-dark-500" />
                        )}
                        <span className={`text-sm font-medium ${getSessionColor(session.session)}`}>
                            {session.session}
                        </span>
                        <span className="text-dark-600 text-xs">•</span>
                        <span className="text-dark-500 text-xs font-mono">
                            {session.time}
                        </span>
                    </div>
                ) : (
                    <div className="flex items-center gap-2">
                        <WifiOff className="w-4 h-4 text-dark-600" />
                        <span className="text-dark-500 text-sm">Connecting...</span>
                    </div>
                )}
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-2">

                {/* Notifications */}

                href="/notifications"
                className="relative p-2 rounded-lg text-dark-400
                hover:text-dark-100 hover:bg-dark-800 transition-colors"
        >
                <Bell className="w-4 h-4" />
                {unreadCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 w-4 h-4
                             bg-red-500 text-white text-xs rounded-full
                             flex items-center justify-center font-medium">
                        {unreadCount > 9 ? "9+" : unreadCount}
                    </span>
                )}
            </a>

            {/* User */}
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg
                        bg-dark-800 text-dark-200">
                <User className="w-4 h-4 text-dark-400" />
                <span className="text-sm font-medium">
                    {user?.username || "User"}
                </span>
            </div>

            {/* Logout */}
            <button
                onClick={() => logout()}
                className="p-2 rounded-lg text-dark-400
                     hover:text-red-400 hover:bg-dark-800 transition-colors"
                title="Logout"
            >
                <LogOut className="w-4 h-4" />
            </button>
        </div>
    </header >
  );
}