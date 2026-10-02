import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BookOpen, CircleHelp, ExternalLink, Search } from "lucide-react";
import { Alert, Card } from "../../components/common";
import { PageWrapper } from "../../components/layout";

const topics = [
    {
        title: "Getting started & accounts",
        faqs: [
            { question: "What is Athena?", answer: "Athena brings market monitoring, options research, AI-assisted analysis, paper trading, backtesting, journaling, and account connections into one workspace." },
            { question: "How do I create an account or sign in with Google?", answer: "Use Create an account on the login page for email and password registration. If the Google button is available, choose it and complete Google's sign-in. If it is missing, ask your administrator to configure the Google OAuth client ID for both the frontend and backend." },
            { question: "I cannot sign in. What should I check?", answer: "Check your username and password, then ask your administrator to confirm the account is active. If your administrator sent a password reset email, open its link and choose a new password. Google sign-in also requires the app's authorized origin to match the address in your browser." },
            { question: "Where can I update my name, email, or timezone?", answer: "Open Settings, then Profile. Changes to the account profile are separate from Google or broker credentials.", links: [{ to: "/settings/profile", label: "Open Profile" }] },
        ],
    },
    {
        title: "Dashboard & charts",
        faqs: [
            { question: "What does the Dashboard show?", answer: "The Dashboard brings the NIFTY 50 chart, market summary, key market panels, and recent signals together. The figures depend on the market-data provider and the latest data it supplies." },
            { question: "How do I change the NIFTY chart interval or view?", answer: "Use the interval selector in the chart header. Choose Candles or Line, drag to pan, scroll to zoom, and use Reset view to return to the default view." },
            { question: "Why can market data look delayed or empty?", answer: "Market data availability depends on your configured provider, instrument coverage, market session, and connection. Check Market Watch and your Zerodha connection if live quotes are expected." },
            { question: "Where can I see other indices and quotes?", answer: "Open Market Watch to view the configured market instruments and their latest quote data.", links: [{ to: "/market", label: "Open Market Watch" }] },
        ],
    },
    {
        title: "Market & options",
        faqs: [
            { question: "How do I inspect an option chain?", answer: "Open Options Workspace, select the underlying and expiry, then review the available strikes, calls, puts, prices, and supported Greeks. The values shown depend on quote and instrument data availability.", links: [{ to: "/market/option-chain", label: "Open Options Workspace" }] },
            { question: "Where can I review historical candles?", answer: "Open Historical Data to choose an instrument and inspect available past candle data. The date range is limited by the data source and stored history.", links: [{ to: "/market/historical", label: "Open Historical Data" }] },
            { question: "Why is an expiry or strike missing?", answer: "The contract must exist in the instrument catalogue and have data available from the selected market provider. Refresh the instrument data or check the underlying and expiry selection." },
            { question: "What do call and put columns mean?", answer: "Calls and puts are displayed on opposite sides of the selected strike. Compare their prices and available Greeks together with the underlying market context; they are research inputs, not trade instructions." },
        ],
    },
    {
        title: "AI Workspace & signals",
        faqs: [
            { question: "How do I run an AI analysis?", answer: "Open AI Workspace, select the instrument and analysis inputs, review the available context, and submit the analysis. Results and prior sessions can be reviewed from the workspace and session history." , links: [{ to: "/analysis", label: "Open AI Workspace" }, { to: "/analysis/history", label: "View session history" }] },
            { question: "Why did the analysis return No Trade?", answer: "No Trade is a valid outcome when the available evidence does not support a sufficiently clear setup. It can also reflect missing or stale market context. Review the reasoning, evidence, and data status before making a decision." },
            { question: "Where do I configure the AI provider?", answer: "Open Settings → AI Connection to select or configure the supported provider connection and test it.", links: [{ to: "/settings/ai-connection", label: "Open AI Connection" }] },
            { question: "Are AI signals guaranteed predictions?", answer: "No. AI output can be incomplete or wrong and should be treated as research assistance. Verify market data and risk independently; Athena does not guarantee an outcome." },
        ],
    },
    {
        title: "Strategies & backtesting",
        faqs: [
            { question: "Where do I view strategy signals?", answer: "Open Strategies to review configured strategies and their available signals. Signal availability depends on the instruments and market data currently loaded.", links: [{ to: "/strategies", label: "Open Strategies" }, { to: "/strategies/signals", label: "View signals" }] },
            { question: "What does backtesting do?", answer: "Backtesting runs configured rule-based strategies against historical candles and archives the resulting runs and metrics. Historical simulation results do not guarantee future performance." },
            { question: "Why is a backtest result unavailable?", answer: "A result is available after a run completes. Failed or still-running entries do not have a completed result to open." , links: [{ to: "/backtest", label: "Open Backtesting" }] },
        ],
    },
    {
        title: "Paper trading & Zerodha",
        faqs: [
            { question: "What is Paper Trading?", answer: "Paper Trading is the simulated portfolio for practice and tracking. Its orders and P&L are separate from orders placed with a broker." },
            { question: "Does using Athena place live broker orders?", answer: "Local development keeps live broker order placement disabled. The Zerodha connection page reports the server's order permission. Never assume a paper order was sent to a broker." , links: [{ to: "/paper", label: "Open Paper Trading" }] },
            { question: "How do I connect Zerodha?", answer: "Open Zerodha Connection, configure the Kite app credentials, start the broker login flow, and complete the redirect back to Athena. Keep the API secret private. Connection status and order permission are shown separately." , links: [{ to: "/zerodha", label: "Open Zerodha Connection" }] },
            { question: "Why is Zerodha connected but order placement disabled?", answer: "Authentication and live-order permission are separate controls. The server can allow quotes and account data while keeping order placement disabled." },
        ],
    },
    {
        title: "Journal, Knowledge & notifications",
        faqs: [
            { question: "What is the Journal for?", answer: "Use Journal to record session notes, trade reflections, outcomes, and lessons learned. Entries help you review your process over time.", links: [{ to: "/journal", label: "Open Journal" }] },
            { question: "What is in the Knowledge Base?", answer: "The Knowledge Base contains saved articles, rules, and prompts available in this workspace. Use it to keep reference material near your research." , links: [{ to: "/knowledge", label: "Open Knowledge Base" }] },
            { question: "How do alerts and notifications work?", answer: "Notifications shows generated messages. Alerts lets you review and manage configured market alerts; notification preferences control supported delivery options." , links: [{ to: "/notifications", label: "Open Notifications" }, { to: "/notifications/alerts", label: "Manage alerts" }, { to: "/notifications/preferences", label: "Notification preferences" }] },
            { question: "Why did I not receive an email notification?", answer: "Email delivery requires the server to have a working email backend and the notification preference to be enabled. In development, the configured console backend prints email content in the backend terminal." },
        ],
    },
    {
        title: "Settings, themes & administration",
        faqs: [
            { question: "How do I change the appearance?", answer: "Use the compact theme selector in the top bar. Your selection is saved in your browser." },
            { question: "Who can see User Management?", answer: "Only staff accounts can see and use User Management. A regular sign-up does not receive staff privileges. Administrators can search users, activate or deactivate accounts, and send password reset links." , links: [{ to: "/admin/users", label: "Open User Management" }] },
            { question: "How does an administrator reset a user's password?", answer: "In User Management, choose Send reset link for an active account with an email address. The user chooses their own new password from the emailed link; staff never see the password. In local development, the console email backend prints the link in the Django terminal." },
            { question: "Why can’t I see User Management or send a reset link?", answer: "Your account needs staff access. Reset messages also require an active user with an email address. Actual email delivery requires a configured email server; local development prints the message to the backend terminal." },
        ],
    },
];

export default function Help() {
    const [search, setSearch] = useState("");
    const normalizedSearch = search.trim().toLowerCase();
    const filteredTopics = useMemo(() => topics.map((topic) => ({
        ...topic,
        faqs: topic.faqs.filter((faq) => `${faq.question} ${faq.answer} ${topic.title}`.toLowerCase().includes(normalizedSearch)),
    })).filter((topic) => topic.faqs.length), [normalizedSearch]);
    const resultCount = filteredTopics.reduce((total, topic) => total + topic.faqs.length, 0);

    return (
        <PageWrapper title="Help & FAQ" subtitle="Guides to Athena’s workspace, tools, and account features">
            <Card className="overflow-hidden">
                <div className="rounded-xl border border-primary-800/50 bg-primary-900/15 p-5 sm:p-6">
                    <div className="flex items-start gap-4">
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-primary-700/50 bg-primary-800/30 text-primary-300"><BookOpen className="h-5 w-5" /></div>
                        <div className="min-w-0 flex-1">
                            <p className="text-sm font-semibold text-dark-100">Find your way around Athena</p>
                            <p className="mt-1 text-sm leading-6 text-dark-400">Search common questions or open a section below. Data availability and enabled features depend on your account and server configuration.</p>
                            <label className="relative mt-4 block max-w-xl">
                                <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-500" aria-hidden="true" />
                                <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search help and FAQ" aria-label="Search help and frequently asked questions" className="h-11 w-full rounded-lg border border-dark-700 bg-dark-950/80 pl-10 pr-4 text-sm text-dark-100 outline-none placeholder:text-dark-500 focus:border-primary-500" />
                            </label>
                            <p className="mt-2 text-xs text-dark-500">{resultCount} {resultCount === 1 ? "answer" : "answers"} found</p>
                        </div>
                    </div>
                </div>

                <div className="mt-6 space-y-6">
                    {filteredTopics.map((topic) => (
                        <section key={topic.title}>
                            <h2 className="mb-3 text-xs font-bold uppercase tracking-[0.14em] text-primary-300">{topic.title}</h2>
                            <div className="divide-y divide-dark-800 rounded-xl border border-dark-800">
                                {topic.faqs.map((faq) => (
                                    <details key={faq.question} className="group px-4 py-4 first:rounded-t-xl last:rounded-b-xl open:bg-dark-900/60">
                                        <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-sm font-semibold text-dark-200 marker:hidden">
                                            <span className="flex items-start gap-3"><CircleHelp className="mt-0.5 h-4 w-4 shrink-0 text-primary-400" aria-hidden="true" />{faq.question}</span>
                                            <span className="text-lg font-normal text-dark-500 transition-transform group-open:rotate-45" aria-hidden="true">+</span>
                                        </summary>
                                        <div className="ml-7 mt-3 text-sm leading-6 text-dark-400">
                                            <p>{faq.answer}</p>
                                            {faq.links?.length > 0 && (
                                                <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
                                                    {faq.links.map((item) => (
                                                        <Link key={item.to} to={item.to} className="inline-flex items-center gap-1 text-xs font-semibold text-primary-400 hover:text-primary-300">
                                                            {item.label}<ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                                                        </Link>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </details>
                                ))}
                            </div>
                        </section>
                    ))}
                    {!filteredTopics.length && <div className="py-12 text-center text-sm text-dark-500"><CircleHelp className="mx-auto mb-3 h-6 w-6" /><p>No answers match that search.</p><button type="button" onClick={() => setSearch("")} className="mt-2 font-semibold text-primary-400 hover:text-primary-300">Clear search</button></div>}
                </div>
            </Card>

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-dark-800 bg-dark-900/50 px-4 py-4">
                <p className="text-sm text-dark-400">Still need help? Contact your Athena administrator with the page name and any error message.</p>
                <Link to="/settings" className="inline-flex items-center gap-2 text-sm font-semibold text-primary-400 hover:text-primary-300">Settings <ExternalLink className="h-4 w-4" aria-hidden="true" /></Link>
            </div>
        </PageWrapper>
    );
}
