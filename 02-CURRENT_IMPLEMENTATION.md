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

### Update: in-app arming (replaces "only the environment can turn it on")

The environment is no longer the only way to allow real orders, because other users need to do it without editing
`.env`. `ZerodhaOrderListAPIView.post()` now calls `LiveTradingService.can_place(user)` and refuses with 403
unless **all** of these hold (market hours and the per-order `confirm_live_order` are still checked after):

1. **Not locked.** `LIVE_TRADING_LOCKED=True` in the server environment forces everything off, whatever the
   database says. This is the emergency stop and can only be set on the server.
2. **Master switch on.** An administrator (`is_staff`) turns "Allow live orders on this installation" on in
   Settings (stored in `LiveTradingControl`, off by default), or the older `LIVE_TRADING_ENABLED=True` flag is set.
   Turning it off cancels every user's arming at once and an old arming does not revive when it is turned back on.
3. **The user is armed.** In Settings the user reads the risk notice, ticks a box and types
   `I UNDERSTAND THE RISKS`. Arming needs a valid Zerodha session, is refused after 15:30 IST, and **lapses at
   15:30 IST the same day**, so it must be redone every day.

The Live orders panel in Settings is hidden until the user has a working Zerodha connection. Arm, disarm and master
changes are recorded in `LiveTradingAuditEvent`. The dashboard's "Real-order permission" tile and the order forms
read `live_orders_enabled`, which now means "this user may send real orders right now". The notice text
(`DISCLAIMER_LINES` in `live_trading_service.py`) is a draft and should be reviewed by someone qualified before
other people use it. Tests: `apps/zerodha/test_live_trading.py` (the safety rules were mutation-checked).

### Manual order ticket

The Dashboard's "Market Read · NIFTY 50" panel has a "Manual order · NIFTY" strip under the AI-selected contract:
Call/Put and ITM/ATM/OTM toggles resolve one real contract from the live option chain (ITM and OTM are one strike
step from the ATM strike), show its symbol, strike, premium, lot size and expiry, and a "Review manual order"
button opens the same "Review live Zerodha order" window as the AI order. It is BUY-only (the risk is the premium
paid), has no AI-signal requirement, and uses every other gate: the user must be armed, the market open,
the NIFTY quote and the contract's own quote under 60 seconds old, and the Zerodha session valid. The review
window defaults to a LIMIT order at the current premium for one lot, needs the acknowledgement tick, and sends
`confirm_live_order`. To test a broker rejection without filling, lower the limit price far below the market.

### Database settings (SQLite by default, PostgreSQL on request)

`DATABASES` is built by `config/database.py` from the environment. With nothing set it is SQLite
(`backend/db.sqlite3`), as before. Set `DATABASE_URL=postgres://user:password@host:5432/dbname` (percent-encode special
characters in the password; `?sslmode=require` is supported) or `DB_ENGINE=postgres` with `DB_NAME`, `DB_USER`,
`DB_PASSWORD`, `DB_HOST`, `DB_PORT` and `DB_SSLMODE` to use PostgreSQL. A URL wins over the separate variables.
Connections are reused for 60 seconds and health-checked. Errors never include the password. Setting these in
`.env` switches the running app on its next restart, so do that only as part of the cutover.

### Moving from SQLite to PostgreSQL (rehearsed and cut over on 2026-10-05)

The test suite (400 tests) passes on both databases. A full rehearsal copied the dev database into an empty
PostgreSQL database: 44 tables, 0 row-count differences, identical checksums, user ids and timestamps (to the
microsecond) preserved, and new rows get fresh ids. The copy tool is `scripts/copy_sqlite_to_postgres.py`
(logic in `shared/db_copy.py`); dumpdata/loaddata is NOT used because it rounds timestamps to milliseconds and
renumbers users. It opens SQLite read-only, refuses to run unless the target is a migrated, empty PostgreSQL
database, and runs in one transaction. It takes about 20 seconds for the dev data.

Things the rehearsal found and fixed: `Instrument.symbol` widened from 50 to 100 characters (4 ETF names were
longer, SQLite ignores the limit but PostgreSQL does not, and the daily instrument import would have failed);
instrument ordering now puts empty values first and breaks ties by trading symbol, so lists come out in the same
order on both databases; the indicators API no longer crashes on NaN. Known harmless difference: PostgreSQL on
Windows sorts text ignoring spaces and dashes, so about 0.6% of instrument rows (obscure fund names) sort slightly
differently.

**Cut over (2026-10-05, evening).** Chosen route: a fresh PostgreSQL database rather than a full copy. The copy tool
gained `--only app.model,...` and was used to carry across just the login data (user accounts, JWT token tables,
the Zerodha connection and the AI provider key); the `Ranthony1` test user was removed. Everything else was
re-fetched from Zerodha: instruments (NSE 10,332, NFO 35,436, the SENSEX index, MCX/CDS driver futures) and the
last 60 days of candles (1d, 30m, 15m, 5m, 3m, 1m) for NIFTY and BANKNIFTY. With only 60 days of daily candles the
gap-direction base rates have far fewer sessions than the earlier 5 years, so they may show "not enough data";
`python manage.py backfill_candles --symbols NIFTY,BANKNIFTY --timeframe 1d --years 5` restores them. AI runs, audit
events and all trading records were deliberately reset. `.env` now has `DATABASE_URL`; deleting that line and
restarting returns to SQLite (the SQLite file and its backups in C:/DevOpsProject/athena-backups were not changed).
First PostgreSQL backup: `athena_db-*.dump` in the same folder (pg_dump custom format; restore with pg_restore).

Original cutover steps, for reference:

Cutover (do it outside market hours):
1. Stop the Django server, Celery worker and Celery beat. Back up `backend/db.sqlite3`.
2. In `.env` set `DATABASE_URL=postgres://athena:PASSWORD@localhost:5432/athena_db` (a strong password).
3. `cd backend`, then `python manage.py migrate` (builds the schema in the empty PostgreSQL database).
4. `python scripts/copy_sqlite_to_postgres.py`, and check it prints "done" with no STOPPED message.
5. Start everything and sign in; reconnect Zerodha (tokens are copied, but check the status).
Rollback: delete the `DATABASE_URL` line and restart. The SQLite file is untouched by all of this. Run
`python manage.py migrate` on SQLite as well if you keep using it.

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

### Gap analysis

`gap_analysis` in the report: today's opening gap, how much price has retraced, and how past sessions with the
same gap category closed against their own open, reported as continued / reversed / flat. These are historical
frequencies from stored daily candles (at least 10 matching sessions, otherwise no base rate), not judgment
estimates. The base rate excludes today's date only.

### Time-block analysis

`time_blocks` in the report: four windows (09:15-10:30, 10:30-12:00, 12:00-13:30, 13:30-15:30) summarised over
the last 20 stored sessions of 15-minute candles: average range, how often the window finished up, and how
directional it was. Labels are descriptive: tendency (leans up / leans down / no consistent lean, needing 60% of
sessions and the same sign of average move), volatility (relative to the other windows) and trend strength
(thresholds are documented constants in `time_block_service.py`, not calibrated). A window needs 5 complete
sessions to be labelled and 10 to avoid the low-confidence flag. Windows are skipped on days with under 80% of
their candles. History depth depends on how many 15-minute candles have been backfilled.

### Data freshness guards

Previous-session pivots and CPR are only produced from a daily candle within 7 days of the session. Older data
returns nothing instead of being shown as "the previous session". Time-block analysis reports the last candle
date it used (`through`) and a `stale` flag when that is over 7 days old. On the development database, Nifty has
about 100 days of 15-minute candles (fine), but Bank Nifty stops at 7 August 2026 and needs a backfill
(`backfill_candles`) before its pivots and time blocks are current.

### What the AI prompt sees

The "Computed Metrics" block in the analysis prompt (and `deterministic_metrics` in the result) now also carries
the Black-76 figures, required moves, straddle Greeks, VIX one-session move, realized vol, historical gap
outcomes, ATM OI change and volume spike from snapshots, and the time blocks. The core figures are computed from
option rows the prompt already fetched (`core_rows`, ATM +/- 5 strikes), so no second chain request is made.
Everything is read-only context; missing values print as NA.

### Profit probability by structure

`GET /api/market/profit-probability/<symbol>/?horizon=15|30|60&mode=LIVE|NEXT_SESSION`, shown on both workspaces
and summarised in the AI prompt. For the ATM call, put and straddle it finds the index move at the exit time that
makes the option(s) worth the entry premium plus costs (Black-76 repricing, time decay, IV held; also shown with
IV -2/+2 vol points). It then counts how often past sessions, entered at the same time of day and held for the
same horizon, moved at least that far. A no-drift lognormal formula is shown beside it as a cross-check.
Brokerage is 20 rupees per order per leg. At least 30 matching sessions are required, otherwise the card says
so and shows no number. "Highest" is only labelled when the leader is 5 points ahead of the runner-up. This
replaces the judgment-based Call/Put/Straddle percentages and the Monte Carlo edge scores of the reference
prompt. It is a historical frequency under stated assumptions, not a forecast. Uses stored 15-minute candles, so
Bank Nifty needs its candle backfill first.

### Filter engine

`GET /api/market/options-engine/<symbol>/?horizon=15|30|60&mode=LIVE|NEXT_SESSION` returns the six filters,
the verdict and the profit probabilities from one set of live inputs; the workspaces show it as the Filter
engine card, and the AI prompt carries a one-line summary. At least 4 of 6 must pass; not evaluable and not
applicable never count as passes. Thresholds are in `EngineParameters` (`filter_engine_service.py`).

| Filter | Rule | Source |
|---|---|---|
| A | Value of the IV change over the window (IV velocity x straddle vega) must exceed 0.6 x theta over the same window, and IV must be rising | reference |
| B | VIX one-session move >= 0.9 x the required move; passes if any structure qualifies (straddle uses its nearer side) | reference |
| C | ATM call or put OI changes by >= 5% over the window (spike or unwind) | Athena proposal |
| D | Realized / implied volatility >= 0.9 (10-session realized) | Athena proposal |
| E | Every evaluable ATM leg's spread narrowed >= 10% | Athena proposal |
| F | Entry before 14:00 IST while the market is open; N/A when closed or next-session | reference |

Verdict is NO_TRADE below 4 passes, otherwise CONDITIONS_MET with the historically strongest structure named only
if profit probability gives a 5-point lead. It is analysis only: no order, basket or sizing is produced. Replaying
the reference run (falling IV, closed market) gives 3 of 6, matching the reference.

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
