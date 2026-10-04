# 02 — CURRENT IMPLEMENTATION STATUS

This is the authoritative "what's actually built" doc. **Regenerate this
file from the real repository regularly** (e.g. extend `generate_claude_md.py`
to populate it from `apps/*/models.py` and migrations) — anything here that
hasn't been re-verified against source should be treated with suspicion.

**Last verified against source:** 2026-09-25 — verified directly against
`apps/*/models.py`, `apps/*/services/`, `apps/*/api/`, migrations, and the
test suite. The previous version of this file significantly understated
what was actually built; treat any future edit to this file with the same
level of direct source verification, not assumption.

---

## Status Legend

- ✅ **IMPLEMENTED** — built and wired end-to-end (model → repository →
  service → API). Does not imply full test coverage, load-testing, or a
  security review — see each module's Notes column.
- 🟡 **PARTIAL** — some work exists, not complete
- ⬜ **PLANNED** — described in `01-ATHENA_APPLICATION_CONTEXT.md`, not started

---

## Module Status Table

| Module | Capability | Status | Notes |
|---|---|---|---|
| accounts | JWT auth: login, logout, profile, refresh, Swagger Bearer, protected API access; registration, Google sign-in, user management, admin-initiated password reset | ✅ IMPLEMENTED | Sign-up policy is set by `REGISTRATION_MODE`: **`approval`** (default; accounts are created inactive and a staff member approves them in User Management, staff are emailed), `open` (sign in immediately) or `closed` (no new accounts; existing users, including Google users, can still sign in). The same rule covers first-time Google sign-in. An unknown value stops the app at startup. Login/Google/reset/register/refresh are rate limited. When staff activate an account the user is emailed a sign-in link (best effort; no password or token). Signed-in users can edit their own name, phone and timezone (`PATCH /api/accounts/profile/`); username, email and privilege flags cannot be changed there. Covered by `accounts/tests.py` (66 tests) |
| platform | CORS | ✅ IMPLEMENTED | Browsers may call the API only from `CORS_ALLOWED_ORIGINS` (comma-separated; dev default is the local Vite origins, production default is none). Credentialed cross-origin requests are off because the frontend authenticates with a JWT header. A wildcard or scheme-less origin fails `manage.py check`. Covered by `config/tests.py` |
| dashboard | Protected dashboard API returning authenticated info + module status | ✅ IMPLEMENTED (basic) | Still a simple status/orchestration endpoint, not a real aggregation of other modules' data |
| market_data | Instrument / Quote / Candle models, serializers, API, services, providers, Django Admin | ✅ IMPLEMENTED | |
| market_data | Repository layer: `base_repository.py`, `instrument_repository.py`, `quote_repository.py`, `candle_repository.py`, `market_repository.py` | ✅ IMPLEMENTED | Previously flagged as "next up" — this is built and in use |
| market_data | Technical indicators: SMA/EMA/WMA, RSI/MACD/Stochastic, Bollinger Bands/ATR, VWAP/OBV, Pivot/CPR | ✅ IMPLEMENTED | `indicators/` package + `IndicatorService`, exposed via `/api/market/indicators/` |
| market_data | Celery background tasks: intraday candle sync, signal-outcome tracking | ✅ IMPLEMENTED | `apps/market_data/tasks.py`, scheduled via `CELERY_BEAT_SCHEDULE` |
| ai_engine | AI interpretation layer, provider abstraction, structured output | ✅ IMPLEMENTED | Providers: mock, Claude, Groq, Kimi (`AI_PROVIDER` setting). Prompt templates, analysis sessions, AI signals all modeled and exposed via API |
| strategies | Deterministic strategy engine (read-only API; execution retired) | 🟡 PARTIAL | EMA crossover, RSI, VWAP, ORB strategies and `StrategyEngine` remain and power backtesting. The API is now read-only: list/detail/signals work, create/update/delete are removed, and `POST /api/strategies/run/` and `/run-all/` return **410 Gone** in favour of the AI Workspace. `StrategyService.create/update/delete/run_strategy/run_all` are no longer reachable from the API. Signals are scoped per user (your own plus unowned legacy signals; never another user's). Covered by `strategies/tests.py` (12 tests) |
| paper_trading | Simulated order/position/P&L engine | ✅ IMPLEMENTED | `BrokerSimulator`, order/position/trade services, brokerage simulation. **Real test coverage** — 367 lines in `tests.py` covering P&L math, including two documented/fixed known issues |
| backtesting | Strategy evaluation against historical data | ✅ IMPLEMENTED | Engine, `ReportService` (win rate, drawdown, Sharpe, expectancy, profit factor, equity curve). **Real test coverage** — 261 lines in `tests.py` |
| journal | Trade journaling | ✅ IMPLEMENTED | Entries, trade notes, lessons/rules, AI review service |
| knowledge | Long-term reference/lesson store | ✅ IMPLEMENTED | Articles, book notes, trading rules, prompt library, search. Articles are private to their owner: reading, summarizing, editing or deleting by slug works only for the author, and another user's slug behaves exactly like a missing one (and never bumps their view count). Covered by `knowledge/tests.py` |
| notifications | Email/Telegram/in-app alerts | ✅ IMPLEMENTED | Preferences, price/strategy/AI-signal alerts. WhatsApp from the original vision doc is not implemented |
| **zerodha** | Zerodha Kite Connect integration — config/session models, token exchange, MCP-backed service layer, live order placement | ✅ IMPLEMENTED | **Not part of the original 10-app list documented below — this is an 11th app that exists in the repo and needs to stay in this list going forward.** Live order placement is hard-gated behind `LIVE_TRADING_ENABLED` — see dedicated section below. Has test coverage for that gate and for the `LIVE_TRADING_ENABLED` setting only (8 tests); the rest of the app's services (`KiteService`, `ZerodhaAuthService`, MCP layer) have no test coverage yet |
| frontend (React) | Login, dashboard, charts, option chain, AI analysis, strategies, paper trading, backtesting, journal, knowledge, notifications, Zerodha, settings | 🟡 PARTIAL | Fully scaffolded — a page, components, a store, and an API client exist per module (`frontend/src/pages/*`, `store/`, `api/`) — but functional correctness against the live backend has not been independently verified as part of any audit to date |
| Live market data / streaming | WebSocket feeds, market depth | 🟡 PARTIAL | `channels`, `daphne`, `channels-redis` are installed and `CHANNEL_LAYERS` is configured in settings, but `config/asgi.py` still only exposes the plain Django ASGI app (`get_asgi_application()`) — there is no `ProtocolTypeRouter`, `routing.py`, or `consumers.py` anywhere in the repo. No WebSocket endpoint is actually reachable, despite the frontend's `useWebSocket.js` expecting one at `ws://.../ws/market/quotes/` |
| Options analysis | OI, PCR, IV, Greeks, ATM/ITM/OTM strikes | ✅ IMPLEMENTED | `option_chain_service.py` computes real Black-Scholes Greeks (delta/gamma/theta/vega) and implied volatility — not placeholder zeros |
| Zerodha MCP integration | Tool-based access to quotes/candles/positions/etc. | ✅ IMPLEMENTED | `apps/zerodha/services/mcp_service.py` (406 lines) backs the entire `KiteService` layer |
| Risk engine | Position sizing, loss limits, exposure limits | ⬜ PLANNED | No `risk_engine`, `RiskService`, or equivalent found anywhere in the codebase (checked via repo-wide search) |

**Do not represent a ⬜ PLANNED item as built, and do not represent a 🟡 PARTIAL
item as complete**, even if `01-ATHENA_APPLICATION_CONTEXT.md` describes it in
full detail — that file is the *vision*, this file is the *status*.

---

## Live Trading Safety Gate

Added 2026-09-25, in response to `apps/zerodha/api/views.py`'s
`ZerodhaOrderListAPIView.post()` being reachable with only standard JWT
auth and no environment-based safeguard against placing a real broker
order.

- **`MARKET_PROVIDER`** (`config/settings/base.py`) now defaults to
  `"mock"`. Only `config/settings/production.py` sets it to `"zerodha"`.
  This controls which market-data provider `market_data/providers/provider_factory.py`
  uses — it does **not** by itself gate order placement.
- **`LIVE_TRADING_ENABLED`** (`config/settings/base.py`) defaults to
  `False`, read from the `LIVE_TRADING_ENABLED` environment variable (only
  the exact value `True` turns it on). `production.py` no longer forces it
  on, so production is also off until the server's environment sets it.
  `development.py` always forces it off. This is the actual gate.
- `ZerodhaOrderListAPIView.post()` checks `settings.LIVE_TRADING_ENABLED`
  directly and unconditionally, before touching the serializer or
  `KiteService`, returning `403 Forbidden` if it's not explicitly `True` —
  **independent of what `MARKET_PROVIDER` resolves to**. This means even a
  misconfigured environment that has `MARKET_PROVIDER="zerodha"` cannot
  place a live order unless `LIVE_TRADING_ENABLED` is also explicitly on.
- To enable live trading in production, set `LIVE_TRADING_ENABLED=True` in
  the server's environment explicitly — there is no other way to turn it
  on. (`development.py` ignores the variable and always keeps it off.)
- Covered by `apps/zerodha/tests.py` (`LiveTradingGateTestCase`): gate
  blocks when disabled, gate allows when enabled, and the existing
  401-on-expired-token behavior is unaffected by the gate.

**Related operational note:** during this work, a real Anthropic API key
and Groq API key were found hardcoded in an early git commit
(`backend/config/settings/base.py`), caught by GitHub's push protection
before ever reaching the remote. History was rewritten with
`git filter-repo` to remove them, and both keys were rotated. Never
hardcode a provider API key directly in a settings file, even
temporarily/locally — always go through `os.getenv(...)` and `.env`, and
double-check `git diff` before committing anything under
`config/settings/`.

---

## Current Development Position

All ten originally-documented Django apps are fully implemented, plus an
eleventh (`zerodha`) that exists in the repo but was previously
undocumented. The project is well past the "market-data / repository
stage" this file previously described.

**What's genuinely still incomplete or missing:**

- **Live market data streaming** — Channels/Daphne are installed and
  configured but not wired to any actual WebSocket route or consumer.
- **Risk engine** — no deterministic position-sizing / loss-limit /
  exposure-limit engine exists yet, despite being a stated core
  requirement in `01-ATHENA_APPLICATION_CONTEXT.md` §19.
- **Test coverage** — `paper_trading`, `backtesting`, `strategies`
  (read-only API / 410 stubs), `accounts` (registration, login, Google
  sign-in, refresh, user management, password reset, throttling, production
  secret-key guard), `ai_engine` and `market_data` (targeted regression
  tests, not full coverage), and `zerodha`'s live-trading gate
  have real tests. `dashboard`, `journal`, `knowledge`, and `notifications`
  still have the default Django test stub only, despite
  several of them containing trading-relevant calculations.
- **Frontend functional verification** — the React app is fully
  scaffolded per module but hasn't been verified end-to-end against the
  live backend as part of any audit.
- **AI learning/feedback loop** (`03-AI_LEARNING_FEEDBACK_SYSTEM.md`) —
  still genuinely unbuilt; nothing in `ai_engine`, `journal`, or
  `backtesting` implements prediction/outcome tracking, confidence
  calibration, or mistake classification yet.

---

## Analysis Data Layer (Nifty / Bank Nifty)

Computed by code and handed to the AI as read-only context. The model
narrates these; it does not produce them. Every metric is `None` ("NA" in
the prompt) when its data is missing; nothing is estimated.

| Metric | Source | Where | Shows NA when |
|---|---|---|---|
| Pivots / CPR | Previous completed **daily** candle (IST) | `DailyLevelsService` | No prior daily candle stored |
| Gap retrace % | Previous close, open, live price | `SessionMetrics.gap_retrace` | Any input missing; gap under 0.10% is "FLAT" |
| VIX change % / intraday high | VIX quote (`close`, `ltp`, `high`) | `SessionMetrics.pct_change` | VIX quote unavailable |
| Up/down-bar volume | Last 20 primary-timeframe candles | `SessionMetrics.volume_confirmation` | Under 5 bars or no volume (index candles carry none) |
| Futures VWAP / volume / OI | Front-month FUT live quote | `FuturesService.snapshot` | Mock provider, no user, or unusable quote |
| Option OI walls | Highest CE OI above / PE OI below spot | `StrikeSelectionService.oi_walls` | No option chain or no OI |
| Premium-matched put | Closest PE premium to a call, within 15% | `StrikeSelectionService.premium_matched_put` | No close match (not yet used by the pipeline) |
| EMA50 per timeframe | Report multi-timeframe block | `AnalysisReportService` | Under 50 candles |
| Breadth | Constituent quotes: Nifty 50 or Bank Nifty (12) | `MarketBreadthService.get_breadth(user, index)` | Under 80% of constituents quoted = low confidence |

- The pivot fix: pivots used to come from the previous 15-minute candle; they now use the previous day.
  The per-row `PIVOT` / `CPR` indicator series are unchanged and remain previous-candle values.
- The Bank Nifty constituent list is a snapshot and must be checked against NSE's published list.
- The metrics are returned as `deterministic_metrics` in the analysis result.
- Not changed: the `volatility_setup_service` all-must-pass gate, the validator's probability overwrites,
  and NEXT_SESSION being forced to NO_SETUP.

### Option snapshots

`OptionSnapshot` (`market_option_snapshots`) stores raw price, bid/ask, volume and OI for ATM +/- 10 strikes of
the nearest expiry for NIFTY and BANKNIFTY. `snapshot_option_chain` runs every 5 minutes in market hours and
needs Celery beat plus a valid Zerodha token for the day; `purge_option_snapshots` removes rows older than 20 days.
History only exists from the day this is deployed.

### AI Bank Nifty Workspace (`/analysis/banknifty`)

A single scrolling page: price strip (futures VWAP/volume/OI, VIX change, gap, breadth), Athena's read,
trend check, levels, sentiment and probability, price expectation and the ATM option snapshot. It reads the
report endpoint (including `key_metrics`) and runs the existing analysis API with paper evaluation off.
`MarketWorkspace` takes the symbol as a prop and also serves `/analysis/nifty`. Both pages end with an expiry and strike card (expiry, days to expiry, lot size, ATM call, premium-matched put) and an open-interest profile (call and put walls, put/call OI, max pain), fed by the report's `options` block. Every missing value shows "NA"
with the reason. The older detailed report now lives at `/analysis/detailed`; `/analysis` is the Athena AI Workspace overview (one card per market with price, VIX, nearest support/resistance and the last analysis, each linking to its workspace).

### Core calculations

`CoreCalculationsService` (report key `core_calculations`, shown as a card on both workspaces): parity forward,
Black-76 IV for the ATM call and put, synthetic straddle and its share of spot, required move to recover the
premium (call, put, straddle up and down), straddle theta (per day and per 15 minutes of trading time), gamma and
vega, the VIX-implied one-session move, 10-session realized volatility, and IV velocity from stored snapshots.
`compute` is pure and tested against the reference report's numbers. Anything without verified inputs is `None`.
IV crush risk and the 2-day realized/implied ratio are not calculated yet.

### Not built yet
- Black-76 IV with a put-call-parity forward, IV velocity, OI change, volume spikes, spread tightening, the six
  filters and the 4-of-6 decision (waiting on the source prompts).
- UI cards for these metrics and an options-engine page.
- Futures in the intraday candle sync; the Kite historical `oi` flag is untested on a live account.
- Never to be built: order or basket templates, Monte Carlo "edge" scores, uncalibrated judgment probabilities.

---

## Operational Concerns for Current Work

### Development Safety
- Prefer mock providers where appropriate — `MARKET_PROVIDER` now
  defaults to `"mock"`; see the Live Trading Safety Gate section above.
- Use paper trading before any live execution.
- Live order placement requires `LIVE_TRADING_ENABLED=True` explicitly —
  see above.
- Separate development and production configuration.
- Never commit secrets — never hardcode a provider API key in a settings
  file; always load it via `os.getenv(...)`.
- Validate environment configuration before enabling live functionality.

### Observability
Maintain visibility into: API errors, provider errors, authentication
failures, broker failures, market-data failures, AI requests/failures,
background task failures, trading events. Never write sensitive information
into logs.
