import { Bell, LogOut, Palette, User, Wifi, WifiOff } from "lucide-react";
import { useLogout } from "../../hooks/useAuth";
import { useSession } from "../../hooks/useMarket";
import useAuthStore from "../../store/authStore";
import useNotificationStore from "../../store/notificationStore";
import useUIStore from "../../store/uiStore";
import { getSessionColor } from "../../utils/helpers";

export default function Topbar() {
    const { user } = useAuthStore();
    const { mutate: logout } = useLogout();
    const { unreadCount } = useNotificationStore();
    const { data: session } = useSession();
    const { theme, setTheme } = useUIStore();

    return (
        <header className="h-[104px] bg-dark-900 border-b border-dark-800 flex items-center justify-between px-6 shrink-0">
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
                        <span className="text-dark-500 text-xs font-mono">{session.time}</span>
                    </div>
                ) : (
                    <div className="flex items-center gap-2">
                        <WifiOff className="w-4 h-4 text-dark-600" />
                        <span className="text-dark-500 text-sm">Connecting...</span>
                    </div>
                )}
            </div>

            <div className="flex items-center gap-2">
                <label
                    className="flex items-center gap-1.5 rounded-lg border border-dark-700 bg-dark-800 px-2 py-1.5 text-dark-400"
                    title="Choose appearance"
                >
                    <Palette className="h-3.5 w-3.5" aria-hidden="true" />
                    <span className="sr-only">Choose appearance</span>
                    <select
                        aria-label="Choose appearance"
                        value={theme}
                        onChange={(event) => setTheme(event.target.value)}
                        className="max-w-[92px] cursor-pointer bg-transparent text-[11px] font-medium text-dark-200 outline-none"
                    >
                        <option value="plum">Plum</option>
                        <option value="ivory">Ivory &amp; Indigo</option>
                        <option value="copper">Copper</option>
                        <option value="aurora">Aurora</option>
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                        <option value="neon">Neon</option>
                    </select>
                </label>

                <a
                    href="/notifications"
                    className="relative p-2 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-800 transition-colors"
                >
                    <Bell className="w-4 h-4" />
                    {unreadCount > 0 && (
                        <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-medium">
                            {unreadCount > 9 ? "9+" : unreadCount}
                        </span>
                    )}
                </a>

                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-dark-800 text-dark-200">
                    <User className="w-4 h-4 text-dark-400" />
                    <span className="text-sm font-medium">{user?.username || "User"}</span>
                </div>

                <button
                    onClick={() => logout()}
                    className="p-2 rounded-lg text-dark-400 hover:text-red-400 hover:bg-dark-800 transition-colors"
                    title="Logout"
                >
                    <LogOut className="w-4 h-4" />
                </button>
            </div>
        </header>
    );
}
