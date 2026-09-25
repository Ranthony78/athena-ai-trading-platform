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
| accounts | JWT auth: login, logout, profile, refresh, Swagger Bearer, protected API access | ✅ IMPLEMENTED | |
| dashboard | Protected dashboard API returning authenticated info + module status | ✅ IMPLEMENTED (basic) | Still a simple status/orchestration endpoint, not a real aggregation of other modules' data |
| market_data | Instrument / Quote / Candle models, serializers, API, services, providers, Django Admin | ✅ IMPLEMENTED | |
| market_data | Repository layer: `base_repository.py`, `instrument_repository.py`, `quote_repository.py`, `candle_repository.py`, `market_repository.py` | ✅ IMPLEMENTED | Previously flagged as "next up" — this is built and in use |
| market_data | Technical indicators: SMA/EMA/WMA, RSI/MACD/Stochastic, Bollinger Bands/ATR, VWAP/OBV, Pivot/CPR | ✅ IMPLEMENTED | `indicators/` package + `IndicatorService`, exposed via `/api/market/indicators/` |
| market_data | Celery background tasks: intraday candle sync, signal-outcome tracking | ✅ IMPLEMENTED | `apps/market_data/tasks.py`, scheduled via `CELERY_BEAT_SCHEDULE` |
| ai_engine | AI interpretation layer, provider abstraction, structured output | ✅ IMPLEMENTED | Providers: mock, Claude, Groq, Kimi (`AI_PROVIDER` setting). Prompt templates, analysis sessions, AI signals all modeled and exposed via API |
| strategies | Deterministic strategy engine | ✅ IMPLEMENTED | EMA crossover, RSI, VWAP, ORB strategies; `StrategyEngine`/`StrategyService`, signal generation and persistence |
| paper_trading | Simulated order/position/P&L engine | ✅ IMPLEMENTED | `BrokerSimulator`, order/position/trade services, brokerage simulation. **Real test coverage** — 367 lines in `tests.py` covering P&L math, including two documented/fixed known issues |
| backtesting | Strategy evaluation against historical data | ✅ IMPLEMENTED | Engine, `ReportService` (win rate, drawdown, Sharpe, expectancy, profit factor, equity curve). **Real test coverage** — 261 lines in `tests.py` |
| journal | Trade journaling | ✅ IMPLEMENTED | Entries, trade notes, lessons/rules, AI review service |
| knowledge | Long-term reference/lesson store | ✅ IMPLEMENTED | Articles, book notes, trading rules, prompt library, search |
| notifications | Email/Telegram/in-app alerts | ✅ IMPLEMENTED | Preferences, price/strategy/AI-signal alerts. WhatsApp from the original vision doc is not implemented |
| **zerodha** | Zerodha Kite Connect integration — config/session models, token exchange, MCP-backed service layer, live order placement | ✅ IMPLEMENTED | **Not part of the original 10-app list documented below — this is an 11th app that exists in the repo and needs to stay in this list going forward.** Live order placement is hard-gated behind `LIVE_TRADING_ENABLED` — see dedicated section below. Has test coverage for that gate only (3 tests); the rest of the app's services (`KiteService`, `ZerodhaAuthService`, MCP layer) have no test coverage yet |
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
  `False`, read from the `LIVE_TRADING_ENABLED` environment variable.
  `production.py` sets it to `True`. This is the actual gate.
- `ZerodhaOrderListAPIView.post()` checks `settings.LIVE_TRADING_ENABLED`
  directly and unconditionally, before touching the serializer or
  `KiteService`, returning `403 Forbidden` if it's not explicitly `True` —
  **independent of what `MARKET_PROVIDER` resolves to**. This means even a
  misconfigured environment that has `MARKET_PROVIDER="zerodha"` cannot
  place a live order unless `LIVE_TRADING_ENABLED` is also explicitly on.
- To enable live trading anywhere outside of `production.py`, set
  `LIVE_TRADING_ENABLED=True` in `.env` explicitly — there is no other way
  to turn it on.
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
- **Test coverage** — only `paper_trading`, `backtesting`, and (narrowly)
  `zerodha`'s live-trading gate have real tests. `accounts`, `ai_engine`,
  `dashboard`, `journal`, `knowledge`, `market_data`, `notifications`, and
  `strategies` still have the default Django test stub only, despite
  several of them containing trading-relevant calculations.
- **Frontend functional verification** — the React app is fully
  scaffolded per module but hasn't been verified end-to-end against the
  live backend as part of any audit.
- **AI learning/feedback loop** (`03-AI_LEARNING_FEEDBACK_SYSTEM.md`) —
  still genuinely unbuilt; nothing in `ai_engine`, `journal`, or
  `backtesting` implements prediction/outcome tracking, confidence
  calibration, or mistake classification yet.

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
