import { NavLink } from "react-router-dom";
import {
    LayoutDashboard,
    TrendingUp,
    Brain,
    Zap,
    Briefcase,
    BookOpen,
    FlaskConical,
    Library,
    Bell,
    Link,
    Settings,
    ChevronLeft,
    Activity,
} from "lucide-react";
import useUIStore from "../../store/uiStore";
import { APP_NAME } from "../../utils/constants";

const navItems = [
    {
        group: "Main",
        items: [
            { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
            { to: "/market", icon: TrendingUp, label: "Market Watch" },
            { to: "/analysis", icon: Brain, label: "AI Analysis" },
            { to: "/strategies", icon: Zap, label: "Strategies" },
        ],
    },
    {
        group: "Trading",
        items: [
            { to: "/paper", icon: Briefcase, label: "Paper Trading" },
            { to: "/journal", icon: BookOpen, label: "Journal" },
            { to: "/backtest", icon: FlaskConical, label: "Backtesting" },
        ],
    },
    {
        group: "Resources",
        items: [
            { to: "/knowledge", icon: Library, label: "Knowledge Base" },
            { to: "/notifications", icon: Bell, label: "Notifications" },
            { to: "/zerodha", icon: Link, label: "Zerodha" },
            { to: "/settings", icon: Settings, label: "Settings" },
        ],
    },
];

export default function Sidebar() {
    const { sidebarOpen, toggleSidebar } = useUIStore();

    return (
        <aside
            className={`
        flex flex-col bg-dark-900 border-r border-dark-800
        transition-all duration-300 shrink-0
        ${sidebarOpen ? "w-56" : "w-16"}
      `}
        >
            {/* Logo */}
            <div className="flex items-center justify-between px-4 h-16 border-b border-dark-800">
                {sidebarOpen && (
                    <div className="flex items-center gap-2">
                        <Activity className="w-5 h-5 text-primary-500" />
                        <span className="font-bold text-dark-50 text-sm">
                            {APP_NAME}
                        </span>
                    </div>
                )}
                <button
                    onClick={toggleSidebar}
                    className="p-1.5 rounded-lg text-dark-400 hover:text-dark-100
                     hover:bg-dark-800 transition-colors ml-auto"
                >
                    <ChevronLeft
                        className={`w-4 h-4 transition-transform duration-300
              ${!sidebarOpen ? "rotate-180" : ""}`}
                    />
                </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-6">
                {navItems.map((group) => (
                    <div key={group.group}>
                        {sidebarOpen && (
                            <p className="text-xs font-semibold text-dark-600
                            uppercase tracking-wider px-2 mb-2">
                                {group.group}
                            </p>
                        )}
                        <ul className="space-y-0.5">
                            {group.items.map((item) => (
                                <li key={item.to}>
                                    <NavLink
                                        to={item.to}
                                        className={({ isActive }) => `
                      flex items-center gap-3 px-2 py-2 rounded-lg
                      text-sm font-medium transition-all duration-150
                      ${isActive
                                                ? "bg-primary-600/20 text-primary-400"
                                                : "text-dark-400 hover:text-dark-100 hover:bg-dark-800"
                                            }
                    `}
                                    >
                                        <item.icon className="w-4 h-4 shrink-0" />
                                        {sidebarOpen && <span>{item.label}</span>}
                                    </NavLink>
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </nav>
        </aside>
    );
}