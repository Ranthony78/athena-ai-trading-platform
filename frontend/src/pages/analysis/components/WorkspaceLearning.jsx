import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, Button, Table, Badge } from "../../../components/common";
import { analysisAPI } from "../../../api/analysis";

const stamp = (value) => value ? new Date(value).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" }) + " IST" : "Unavailable";
const number = (value) => value == null ? "N/A" : Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 });

export function RecentAnalysis({ refreshKey }) {
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(0);
    const [selected, setSelected] = useState(null);
    const { data = [], isLoading, isError } = useQuery({
        queryKey: ["ai-sessions", refreshKey], queryFn: () => analysisAPI.getSessions(),
        select: (res) => res.data.data, staleTime: 30_000,
    });
    const filtered = data.filter((row) => [row.symbol, row.timeframe, row.status, row.parsed_output?.reasoning].some((value) => String(value || "").toLowerCase().includes(search.toLowerCase())));
    const currentPage = Math.min(page, Math.max(0, Math.ceil(filtered.length / 5) - 1));
    const columns = [
        { key: "session_time", label: "Time", render: stamp },
        { key: "symbol", label: "Market" },
        { key: "timeframe", label: "Interval" },
        { key: "forecast_horizon_minutes", label: "Horizon", render: (value) => value ? `${value} min` : "Unavailable" },
        { key: "parsed_output", label: "Key insight", render: (value) => <span className="analysis-recent-insight">{value?.reasoning || value?.market_view || value?.signal || "No insight recorded"}</span> },
        { key: "status", label: "Status", render: (value) => <Badge variant={value === "COMPLETE" ? "green" : value === "FAILED" ? "red" : "gray"}>{value}</Badge> },
        { key: "id", label: "Action", render: (value) => <Button size="sm" variant="secondary" onClick={() => setSelected(selected === value ? null : value)}>View</Button> },
    ];
    return <Card title="Recent Analysis" actions={<a className="btn-secondary btn-sm" href="/analysis/history">View analysis history</a>}>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <input type="search" aria-label="Search recent analyses" placeholder="Search saved analyses…" className="input max-w-xs" value={search} onChange={(event) => { setSearch(event.target.value); setPage(0); }} />
            {filtered.length > 5 && <div className="flex items-center gap-2 text-xs text-dark-400"><Button size="sm" variant="secondary" disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>Previous</Button><span>{currentPage + 1} / {Math.ceil(filtered.length / 5)}</span><Button size="sm" variant="secondary" disabled={(currentPage + 1) * 5 >= filtered.length} onClick={() => setPage(currentPage + 1)}>Next</Button></div>}
        </div>
        {isError ? <p role="alert" className="text-sm text-red-400">Recent analyses could not be loaded.</p> : <Table columns={columns} data={filtered.slice(currentPage * 5, currentPage * 5 + 5)} loading={isLoading} emptyTitle="No saved analyses" emptyDescription="Your saved requests will appear here after an analysis." />}
        {selected && <SavedRequest key={selected} sessionId={selected} />}
    </Card>;
}

export function MarketDriversPanel({ snapshot, compact = false }) {
    const { data, isLoading, isError } = useQuery({
        queryKey: ["market-drivers"], queryFn: () => analysisAPI.getMarketDrivers(),
        select: (res) => res.data.data, enabled: !snapshot, staleTime: 300_000,
    });
    const packet = snapshot || data;
    return <Card className={compact ? "h-full min-w-0" : ""} title="Market Drivers" subtitle={snapshot ? "Evidence captured for this AI request" : "News coverage before analysis · no AI request"}>
        {isLoading && <p className="text-sm text-dark-300">Loading source coverage…</p>}
        {isError && !snapshot && <p className="text-sm text-amber-300">Source coverage could not be loaded.</p>}
        {packet?.market_quotes?.length > 0 && <div className="grid gap-2 grid-cols-2 mb-3">
            {packet.market_quotes.map((quote) => <div key={quote.label} className="rounded-lg border border-dark-700 bg-dark-900/40 p-3">
                <div className="flex flex-wrap items-start justify-between gap-1">
                    <h4 className="text-xs font-semibold text-dark-100">{quote.label}</h4>
                    <span className={`text-xs ${quote.status === "fresh" ? "text-emerald-300" : "text-amber-300"}`}>{quote.status === "fresh" ? "Current quote" : quote.status === "stale_or_unverified" ? "Stale / unverified" : "Unavailable"}</span>
                </div>
                <p className="mt-2 font-mono text-sm text-dark-100">{quote.status === "fresh" ? number(quote.ltp) : quote.last_ltp != null ? `Last ${number(quote.last_ltp)} · not current evidence` : "Unavailable"}</p>
                <details className="mt-2"><summary className="cursor-pointer text-xs text-dark-400">Quote time: {stamp(quote.quote_time)} · source</summary>
                <p className="mt-1 text-xs text-dark-400">{quote.source || "Zerodha Kite"}{quote.exchange ? ` · ${quote.exchange}` : ""}{quote.contract ? ` · ${quote.contract}` : ""}{quote.expiry ? ` · expires ${quote.expiry}` : ""}</p>
                <p className="mt-1 text-xs text-dark-400">Quote time: {stamp(quote.quote_time)}</p>
                {quote.reason && <p className="mt-2 text-xs text-amber-300">{quote.reason}</p>}
                </details>
            </div>)}
        </div>}
        {compact && <div className="grid gap-2 sm:grid-cols-2">
            {packet?.topics?.filter((topic) => ["Global markets", "Indian market and sectors"].includes(topic.label)).map((topic) => <div key={topic.key} className="rounded-lg border border-dark-700 p-2">
                <h4 className="text-xs font-semibold text-dark-100">{topic.label}</h4>
                <p className="mt-1 text-xs text-dark-400">{topic.status === "available" ? "Recent sourced news · expand sources below" : "Unavailable · no recent verified coverage"}</p>
            </div>)}

        </div>}
        <details className="mt-3" open={!compact}><summary className="cursor-pointer text-xs text-dark-400">All driver sources, news and coverage limits</summary>
        <div className={compact ? "grid gap-2 sm:grid-cols-2" : "grid gap-3 md:grid-cols-2 xl:grid-cols-3"}>
            {packet?.topics?.map((topic) => <div key={topic.key} className="rounded-lg border border-dark-700 p-3">
                <h4 className="text-sm font-semibold text-dark-100">{topic.label}</h4>
                <p className="text-xs text-dark-300 mt-1">{topic.status === "available" ? "Recent sourced news" : "Unavailable"}</p>
                {topic.reason && <p className="text-xs text-dark-400 mt-2">{topic.reason}</p>}
                <details className="mt-2"><summary className="cursor-pointer text-xs text-dark-400">Sources and limitations</summary>
                {topic.articles?.map((article, index) => <div key={index} className="mt-3 text-xs">
                    {article.url ? <a className="text-primary-400 underline" href={article.url} target="_blank" rel="noopener noreferrer">{article.title}</a> : <span className="text-dark-300">{article.title}</span>}
                    <p className="text-dark-400 mt-1">{article.source || "Unknown source"} · {stamp(article.published_at)}</p>
                    {!article.usable && <p className="text-amber-300">Stale or unverified · excluded as current evidence</p>}
                </div>)}
                <p className="text-xs text-dark-400 mt-3">{topic.limitation}</p>
                </details>
            </div>)}
        </div>
        {packet && <div className="grid gap-3 md:grid-cols-2 mt-3">
            {[["Global market prices", packet.global_market_prices], ["Scheduled event calendar", packet.event_calendar]].map(([label, item]) => <div key={label} className="rounded-lg border border-dark-700 bg-dark-900/30 p-3">
                <h4 className="text-sm font-semibold text-dark-100">{label}</h4>
                <p className="mt-1 text-xs text-amber-300">{item?.status === "available" ? "Available" : "Unavailable"}</p>
                <p className="mt-2 text-xs text-dark-400">{item?.reason || "No verified source is connected."}</p>
                {item?.source && <p className="mt-2 text-[10px] text-dark-500">Source: {item.source}{item.published_at ? ` · ${stamp(item.published_at)}` : ""}</p>}
            </div>)}
        </div>}
        {packet && <p className="mt-3 text-xs text-dark-400">{packet.source} · Assembled {stamp(packet.as_of)}. {packet.note}</p>}
        </details>
    </Card>;
}

export function DecisionEvidence({ result }) {
    return <Card title="AI interpretation and uncertainty" subtitle="Qualitative interpretation; confidence is not a calibrated probability of profit">
        <p className="text-sm text-dark-100">Market view: {result.market_view || "UNCERTAIN"}</p>
        <div className="grid gap-3 md:grid-cols-3 mt-3">
            {Object.entries(result.scenarios || {}).map(([name, description]) => <div key={name} className="border border-dark-700 rounded-lg p-3">
                <h4 className="text-sm font-medium text-dark-200 capitalize">{name} scenario</h4><p className="mt-2 text-sm text-dark-300">{description}</p>
            </div>)}
        </div>
        <div className="grid gap-4 md:grid-cols-2 mt-4">
            {[["Supporting evidence", "supporting_evidence"], ["Conflicting evidence", "conflicting_evidence"], ["What invalidates the view", "invalidation_conditions"], ["Missing information", "missing_information"]].map(([label, key]) => <div key={key}>
                <h4 className="text-sm font-semibold text-dark-200">{label}</h4>
                <ul className="mt-2 space-y-1 text-sm text-dark-300">{result[key]?.length ? result[key].map((item, index) => <li key={index}>• {item}</li>) : <li>Not supplied by the model.</li>}</ul>
            </div>)}
        </div>
        <p className="text-xs text-dark-400 mt-4">Prior resolved observations supplied: {result.prior_outcomes?.sample_size ?? 0}. {result.prior_outcomes?.note}</p>
    </Card>;
}

export function SavedRequest({ sessionId }) {
    const { data, isLoading, isError } = useQuery({queryKey:["saved-ai-request", sessionId], queryFn:()=>analysisAPI.getSession(sessionId), select:(res)=>res.data.data});
    if (isLoading) return <p className="text-sm text-dark-300">Loading saved request…</p>;
    if (isError) return <p className="text-sm text-amber-300">Saved request unavailable.</p>;
    const usesBuiltInPrompt = !data.template_name && (data.prompt_version || "").endsWith("/default");
    return <div className="mt-4 space-y-3 text-sm text-dark-300">
        <p>Analysis #{data.id} · {stamp(data.session_time)} · {data.provider_used || "Legacy provider not recorded"}/{data.model_used} · {data.prompt_version || "Legacy prompt"}</p>
        <p className={usesBuiltInPrompt ? "text-amber-300" : "text-emerald-300"}>
            {usesBuiltInPrompt ? "Built-in versioned prompt used; no active database template was attached." : `Database template used: ${data.template_name || "template metadata unavailable"}.`}
        </p>
        <p className="text-xs break-all">Prompt SHA-256: {data.prompt_hash || "Not recorded for this older request"}</p>
        {data.error_message && <p className="text-red-300">{data.error_message}</p>}
        {[["System prompt", data.system_prompt], ["User prompt / evidence", data.user_prompt], ["Validated output", JSON.stringify(data.parsed_output, null, 2)]].map(([label, value]) => <details key={label} className="border border-dark-700 rounded-lg p-3">
            <summary className="cursor-pointer text-dark-100">{label}</summary><pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap break-words text-xs">{value || "Not recorded"}</pre>
        </details>)}
    </div>;
}

export default function WorkspaceLearning({ symbol, horizon, refreshKey, compact = false }) {
    const [selected, setSelected] = useState(null);
    const {data, isLoading, isError, refetch} = useQuery({queryKey:["ai-learning", symbol, horizon, refreshKey], queryFn:()=>analysisAPI.getLearning(symbol, horizon), select:(res)=>res.data.data, refetchInterval:60_000});
    const paper = data?.paper;
    return <Card className={compact ? "analysis-paper-learning h-full min-w-0" : ""} title="Prediction journal and paper learning" subtitle={`${symbol} · ${horizon}-minute horizon · your analyses only`} actions={<Button size="sm" variant="secondary" onClick={()=>refetch()}>Refresh outcomes</Button>}>
        {isLoading && <p className="text-sm text-dark-300">Loading evaluation history…</p>}
        {isError && <p className="text-sm text-amber-300">Evaluation history could not be loaded. Check the backend and database migrations.</p>}
        {data && <>
            <p className={`analysis-worker-status text-xs ${data.worker?.active ? "text-green-400" : "text-amber-300"}`}>{data.worker?.active ? "Evaluation worker responding" : "Evaluation worker offline or heartbeat overdue"} · Last run: {stamp(data.worker?.heartbeat_at)}</p>
            <div className={compact ? "grid gap-3 sm:grid-cols-3 my-4" : "grid gap-3 grid-cols-2 md:grid-cols-4 my-4"}>
                {[["Saved analyses", data.analyses], ["Paper wins / losses", `${paper.wins} / ${paper.losses}`], ["Realized paper net P&L", `₹${number(paper.net_pnl)}`], ["Realized maximum drawdown", `₹${number(paper.max_drawdown)}`]].filter((_, index) => !compact || index < 3).map(([label,value])=><div key={label} className="rounded-lg border border-dark-700 p-3"><p className="text-xs text-dark-400">{label}</p><p className="text-xl font-semibold text-dark-100 mt-1">{value}</p></div>)}
            </div>
            <details className="mt-3 text-xs text-dark-400"><summary className="cursor-pointer">Paper assumptions and No Trade outcomes · drawdown ₹{number(paper.max_drawdown)}</summary>
            <p className="mt-2 text-xs text-dark-400">{paper.note} Win rate: {number(paper.win_rate)}{paper.win_rate != null ? "%" : ""} · Breakeven: {paper.breakeven}. Taxes are excluded; fill slippage is simulated.</p>
            <p className="mt-3 text-sm text-dark-300">Resolved No Trade: {data.no_trade.resolved} · Subsequent up/down/sideways: {data.no_trade.subsequent_moves.UP || 0}/{data.no_trade.subsequent_moves.DOWN || 0}/{data.no_trade.subsequent_moves.SIDEWAYS || 0}. {data.no_trade.note}</p>
            </details>
            <details className="mt-4 border border-dark-700 rounded-lg p-3"><summary className="cursor-pointer text-sm text-dark-100">Performance by model, instrument, timeframe, market view and prompt</summary>
                <div className="overflow-auto mt-3"><table className="w-full text-xs text-dark-300"><thead><tr><th className="text-left p-2">Group</th><th>Outcomes</th><th>Direction accuracy</th><th>Brier ↓</th></tr></thead><tbody>{data.breakdown.map((row,index)=><tr key={index} className="border-t border-dark-700"><td className="p-2">{row.dimension}: {row.value}{row.limited_sample ? " · limited sample" : ""}</td><td className="text-center">{row.sample_size}</td><td className="text-center">{number(row.direction_accuracy_pct)}{row.direction_accuracy_pct != null ? "%" : ""} (n={row.directional_samples})</td><td className="text-center">{row.brier ?? "N/A"}</td></tr>)}</tbody></table></div>
                {!data.breakdown.length && <p className="text-xs text-dark-400 mt-2">No resolved outcomes yet.</p>}
            </details>
            <details className="mt-4"><summary className="cursor-pointer text-sm text-dark-300">Calibration experiment and recent analyses</summary>
            <div className="mt-4 border border-dark-700 rounded-lg p-3"><h4 className="text-sm text-dark-100">Calibration experiment · {data.candidate.status}</h4><p className="text-xs text-dark-300 mt-2">{data.candidate.note}</p>{data.candidate.status === "evaluated" && <p className="text-xs text-dark-300 mt-2">Train n={data.candidate.training_samples} · validation n={data.candidate.validation_samples} · baseline Brier {data.candidate.baseline_brier} · candidate {data.candidate.candidate_brier}</p>}<p className="text-xs text-dark-400 mt-2">Production probabilities and trading rules are not changed automatically.</p></div>
            <div className="overflow-auto mt-4"><table className="w-full text-sm text-dark-300"><thead><tr><th className="text-left p-2">Analysis / time</th><th className="text-left">Decision</th><th className="text-left">Market outcome</th><th className="text-left">Paper evaluation</th></tr></thead><tbody>
                {data.recent.map((row)=><tr key={row.id} className="border-t border-dark-700"><td className="p-2"><button className="text-primary-400 underline" onClick={()=>setSelected(row.id)}>#{row.id} · {stamp(row.time)}</button></td><td>{row.decision}<p className="text-xs text-dark-400 max-w-xs">{row.reason}</p></td><td>{row.outcome}</td><td>{row.paper?.status || "Not requested"}<p className="text-xs text-dark-400 max-w-xs">{row.paper?.reason}</p>{row.paper?.net_pnl != null && <span>₹{number(row.paper.net_pnl)}</span>}</td></tr>)}
            </tbody></table></div>
            {!data.recent.length && <p className="text-sm text-dark-300 mt-3">Run an analysis to start your prediction journal. No Trade is recorded too.</p>}
            </details>
            {selected && <SavedRequest key={selected} sessionId={selected} />}
        </>}
    </Card>;
}
