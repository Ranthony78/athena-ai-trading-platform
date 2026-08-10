import { Routes, Route, Navigate } from "react-router-dom";
import PrivateRoute from "./PrivateRoute";

// Auth
import Login from "../pages/auth/Login";

// Dashboard
import Dashboard from "../pages/dashboard/Dashboard";

// Market
import MarketWatch from "../pages/market/MarketWatch";
import OptionChain from "../pages/market/OptionChain";
import Historical from "../pages/market/Historical";

// Analysis
import AnalysisReport from "../pages/analysis/AnalysisReport";
import SessionHistory from "../pages/analysis/SessionHistory";

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

export default function AppRouter() {
    return (
        <Routes>
            {/* Public */}
            <Route path="/login" element={<Login />} />

            {/* Protected */}
            <Route element={<PrivateRoute />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />

                {/* Market */}
                <Route path="/market" element={<MarketWatch />} />
                <Route path="/market/option-chain" element={<OptionChain />} />
                <Route path="/market/historical" element={<Historical />} />

                {/* Analysis */}
                <Route path="/analysis" element={<AnalysisReport />} />
                <Route path="/analysis/report" element={<Navigate to="/analysis" replace />} />
                <Route path="/analysis/history" element={<SessionHistory />} />

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
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
    );
}