import { Routes, Route, Navigate } from "react-router-dom";
import PrivateRoute from "./PrivateRoute";

// Auth
import Login from "../pages/auth/Login";
import ResetPassword from "../pages/auth/ResetPassword";

// Dashboard
import Dashboard from "../pages/dashboard/Dashboard";

// Market
import MarketWatch from "../pages/market/MarketWatch";
import OptionChain from "../pages/market/OptionChain";
import Historical from "../pages/market/Historical";

// Analysis
import AnalysisReport from "../pages/analysis/AnalysisReport";
import SessionHistory from "../pages/analysis/SessionHistory";
import WorkspaceOverview from "../pages/analysis/workspace/WorkspaceOverview";
import MarketWorkspace from "../pages/analysis/workspace/MarketWorkspace";

// Strategies
import Strategies from "../pages/strategies/Strategies";
import Signals from "../pages/strategies/Signals";

// Paper Trading
import Portfolio from "../pages/paper/Portfolio";
import Orders from "../pages/paper/Orders";
import Positions from "../pages/paper/Positions";
import Trades from "../pages/paper/Trades";

// Journal
import Journal from "../pages/journal/Journal";
import JournalEntry from "../pages/journal/JournalEntry";
import Lessons from "../pages/journal/Lessons";

// Backtesting
import Backtesting from "../pages/backtesting/Backtesting";
import BacktestResult from "../pages/backtesting/BacktestResult";

// Knowledge
import Knowledge from "../pages/knowledge/Knowledge";
import ArticleDetail from "../pages/knowledge/ArticleDetail";
import Rules from "../pages/knowledge/Rules";
import Prompts from "../pages/knowledge/Prompts";

// Notifications
import Notifications from "../pages/notifications/Notifications";
import Alerts from "../pages/notifications/Alerts";
import Preferences from "../pages/notifications/Preferences";

// Zerodha
import ZerodhaConnect from "../pages/zerodha/ZerodhaConnect";
import ZerodhaOrders from "../pages/zerodha/ZerodhaOrders";
import ZerodhaPositions from "../pages/zerodha/ZerodhaPositions";

// Settings
import Settings from "../pages/settings/Settings";
import Profile from "../pages/settings/Profile";
import AIConnection from "../pages/settings/AIConnection";
import UserManagement from "../pages/settings/UserManagement";
import Help from "../pages/help/Help";

export default function AppRouter() {
    return (
        <Routes>
            {/* Public */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Login />} />
            <Route path="/reset-password" element={<ResetPassword />} />

            {/* Protected */}
            <Route element={<PrivateRoute />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />

                {/* Market */}
                <Route path="/market" element={<MarketWatch />} />
                <Route path="/market/option-chain" element={<OptionChain />} />
                <Route path="/market/historical" element={<Historical />} />

                {/* Analysis */}
                <Route path="/analysis" element={<WorkspaceOverview />} />
                <Route path="/analysis/detailed" element={<AnalysisReport />} />
                <Route
                    path="/analysis/report"
                    element={<Navigate to="/analysis/detailed" replace />}
                />
                <Route path="/analysis/history" element={<SessionHistory />} />
                <Route
                    path="/analysis/nifty"
                    element={<MarketWorkspace symbol="NIFTY" title="AI Nifty Workspace" />}
                />
                <Route
                    path="/analysis/banknifty"
                    element={<MarketWorkspace symbol="BANKNIFTY" title="AI Bank Nifty Workspace" />}
                />

                {/* Strategies */}
                <Route path="/strategies" element={<Strategies />} />
                <Route path="/strategies/signals" element={<Signals />} />

                {/* Paper Trading */}
                <Route path="/paper" element={<Portfolio />} />
                <Route path="/paper/orders" element={<Orders />} />
                <Route path="/paper/positions" element={<Positions />} />
                <Route path="/paper/trades" element={<Trades />} />

                {/* Journal */}
                <Route path="/journal" element={<Journal />} />
                <Route path="/journal/:id" element={<JournalEntry />} />
                <Route path="/journal/lessons" element={<Lessons />} />

                {/* Backtesting */}
                <Route path="/backtest" element={<Backtesting />} />
                <Route path="/backtest/:id" element={<BacktestResult />} />

                {/* Knowledge */}
                <Route path="/knowledge" element={<Knowledge />} />
                <Route path="/knowledge/articles/:slug" element={<ArticleDetail />} />
                <Route path="/knowledge/rules" element={<Rules />} />
                <Route path="/knowledge/prompts" element={<Prompts />} />

                {/* Notifications */}
                <Route path="/notifications" element={<Notifications />} />
                <Route path="/notifications/alerts" element={<Alerts />} />
                <Route path="/notifications/preferences" element={<Preferences />} />

                {/* Zerodha */}
                <Route path="/zerodha" element={<ZerodhaConnect />} />
                <Route path="/zerodha/orders" element={<ZerodhaOrders />} />
                <Route path="/zerodha/positions" element={<ZerodhaPositions />} />

                {/* Settings */}
                <Route path="/settings" element={<Settings />} />
                <Route path="/settings/profile" element={<Profile />} />
                <Route path="/settings/ai-connection" element={<AIConnection />} />
                <Route path="/admin/users" element={<UserManagement />} />
                <Route path="/help" element={<Help />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
    );
}
