# 01 — ATHENA APPLICATION CONTEXT

Full product vision, module capabilities, and target architecture. This is
the *intent* document — cross-check every claim against
`02-CURRENT_IMPLEMENTATION.md` and the actual source before assuming
anything here is built.

---

## 1. Core Product Philosophy

Athena assists decision-making; it does not treat AI output as guaranteed
market truth. The platform distinguishes seven layers that must remain
architecturally separate:

1. Raw market data
2. Derived market indicators
3. Strategy signals
4. AI interpretation
5. Risk assessment
6. Trade recommendation
7. Trade execution

---

## 2. User Management

- Django authentication + custom User model + DRF + JWT access/refresh tokens
- Login, logout, profile, token refresh, protected APIs, user preferences
- Future: role-based permissions

## 3. Dashboard

Primary user view, combining: market status, index prices, market direction,
watchlists, open paper trades, P&L, AI market assessment, strategy signals,
risk alerts, recent trades, notifications. The dashboard **orchestrates**
information from other services — it does not own market or trading logic.

## 4. Market Data Engine

Responsible for obtaining, storing, normalising, and serving financial-market
information. Core concepts: **Instrument, Quote, Candle**.

Future capabilities: historical candles, live quotes, market depth, option
chains, open interest, volume, expiry information, index data, market
breadth, sector information, volatility information.

Flow: `Provider → Market Service → Repository → Django ORM → Database`.
API consumers interact with services, never directly with broker APIs.

## 5. Instrument Management

An Instrument represents a tradable or market-observable security
(BANKNIFTY, NIFTY, equities, futures, calls, puts). Possible fields: trading
symbol, exchange, instrument token, exchange token, instrument type, segment,
expiry, strike, lot size, tick size.

**Always check the existing `market_data` models before changing or adding
fields — never recreate an Instrument model.** The existing model is the
source of truth.

## 6. Live Market Data

Should eventually support live quote retrieval, streaming (WebSocket),
price updates, volume, open interest, bid/ask, market depth. Streaming
infrastructure stays separated from persistence and business logic; caching
and async processing may be required to handle tick frequency.

## 7. Historical Market Data

Represented through Candle records, needed for charting, indicators,
strategy evaluation, backtesting, AI context, and research. Typical
timeframes: 1m, 3m, 5m, 15m, 30m, 60m, daily. Timeframe handling must be
implemented consistently across repositories, services, and APIs.

## 8. Options Analysis (future)

Calls, puts, strike prices, expiries, open interest, change in OI, volume,
implied volatility, PCR, option Greeks, ATM/ITM/OTM strikes. Feeds both the
deterministic strategy engine and the AI engine.

## 9. Technical Analysis

Deterministic indicators: SMA, EMA, RSI, MACD, VWAP, ATR, ADX, Bollinger
Bands, Supertrend, Pivot Points, CPR. **An indicator calculation must never
depend on an LLM.** The AI engine may interpret indicators but does not
replace the calculation.

## 10. Strategy Engine

Converts market conditions into structured trading signals. Types:
trend-following, breakout, opening range breakout, VWAP, EMA, momentum,
mean reversion, options strategies, intraday, swing. Every strategy defines:
inputs, entry conditions, exit conditions, stop-loss logic, target logic,
risk constraints, applicable instruments, applicable timeframes. Results
must be structured data, not only natural-language AI output.

## 11. AI Engine

Interprets structured information from the rest of the platform.

**Inputs:** current price, historical candles, technical indicators, market
trend, option-chain info, OI, volatility, strategy signals, news, sentiment,
existing positions, risk information.

**Outputs:** market bias, bullish/bearish/sideways probability, trade
scenarios, risk observations, entry-zone analysis, stop-loss reasoning,
target scenarios, confidence score, explanation — preferably as structured
output the rest of the app can consume reliably.

### AI Must Not Control Raw Market Data
The LLM is not the source of market truth. Prices come from market-data
providers, indicators from deterministic calculation, balances/positions
from the broker/trading engine. If required information is unavailable,
the system reports that it's unavailable — it does not let the model
fabricate values.

### AI Provider Architecture
Not permanently tied to one LLM provider — should support OpenAI, Anthropic,
Google, local models via a provider abstraction. Prompts are version
controlled; changes to an analytical prompt are treated as application
changes, not casual text edits.

## 12. Zerodha Integration

Initial broker/market integration, potentially providing: authentication,
instrument info, quotes, historical candles, positions, holdings, funds,
orders, order status, live streams. Zerodha MCP integration has been
discussed as an important component.

```
Athena → Provider/Broker Interface → Zerodha Integration → Zerodha Services
```

Zerodha-specific code must stay behind the abstraction boundary — other
modules should not scatter direct Zerodha API calls.

## 13. MCP (Model Context Protocol)

Intended to provide controlled access between AI workflows and external
capabilities — tools such as retrieve quote / candles / option chain /
positions / holdings / funds / orders / market info. The AI should call
tools for factual data rather than rely on model memory for current market
information; tool results become context for AI analysis.

## 14. Paper Trading

Major safety/development component. Strategies must be able to run against
a simulated environment before live trading is mature. Supports: buy/sell,
market/limit/stop-loss orders, positions, average price, realised/unrealised
P&L, brokerage simulation, slippage, trade history. Uses the same high-level
trading interfaces as live trading so strategies aren't rewritten when
moving from simulation to broker-backed execution.

## 15. Backtesting

Evaluates strategies against historical data. Metrics: total/winning/losing
trades, win rate, gross profit/loss, net P&L, max drawdown, average
winner/loser, risk/reward, expectancy, profit factor. Results must be
reproducible — numerical results come from deterministic logic; the AI
engine may explain results but does not calculate them.

## 16. Trading Journal

Records: trade, strategy, entry reason, exit reason, screenshot, notes,
mistakes, lessons learned, market conditions, performance. AI may eventually
analyse journal history for recurring behavioural or strategy patterns.

## 17. Knowledge Module

Long-term contextual store: trading rules, strategy documentation, research,
market notes, lessons, prompt templates, reference material. Must stay
distinguishable from live market data — historical knowledge is never
mistaken for current market information.

## 18. Notifications

Channels: email, Telegram, WhatsApp, in-app. Triggers: price conditions,
strategy signals, risk events, position changes, AI analysis, system events.
Notification delivery never contains the underlying trading business logic.

## 19. Risk Philosophy

No trading signal is complete without risk context. Risk controls: position
sizing, maximum loss, stop loss, daily loss limits, exposure limits, max
concurrent positions, instrument-specific limits, strategy-specific limits.
Deterministic wherever possible — **an AI model must never be able to
bypass mandatory risk controls.**

## 20. Target Analysis Workflow

```
Market Data → Indicators → Option Analysis → Strategy Engine →
News/Sentiment → Risk Engine → AI Engine → Structured Market Assessment →
User → Paper Trade / Approved Execution
```

Implement incrementally — do not attempt the entire workflow in one change.

## 21. Target Trade Analysis Output (shape)

```
Market: BANK NIFTY
Market Regime: Bullish / Bearish / Sideways / Volatile
Probability: Bullish % / Bearish % / Sideways %
Technical Evidence: Trend, Momentum, VWAP, RSI, MACD, Support, Resistance
Options Evidence: OI, PCR, IV, Key strikes
Risk: Low / Medium / High
Scenarios: Bullish / Bearish / No-trade
Confidence: 0–100
Explanation: human-readable reasoning
```

Preserve the distinction between factual inputs and AI-generated
interpretation in this output.

---

## 22. Backend Technology

Python, Django, Django REST Framework, Simple JWT, drf-spectacular,
django-cors-headers, python-dotenv. Exposes REST APIs for the React
frontend and potentially other clients.

## 23. Frontend

Dedicated `frontend/` area, React. Should ultimately provide: login,
dashboard, market watch, charts, option-chain views, AI analysis, strategy
management, paper trading, backtesting, journal, knowledge, notifications,
user settings. Consumes backend APIs — trade/risk/market calculation logic
is never duplicated in React.

## 24. Database

Django ORM primary access path; SQLite (`db.sqlite3`) used during
development. Avoid unnecessary DB-specific logic so the database can evolve
without rewriting business logic. Before any DB change: inspect existing
models, migrations, and repositories; determine whether the field/table
already exists; preserve existing data; avoid duplicate models.

## 25. Repository Pattern

```
API → Service → Repository → Django ORM → Database
```

Repositories handle persistence-oriented operations
(`InstrumentRepository`, `QuoteRepository`, `CandleRepository`). A shared
`BaseRepository` may provide common operations; domain-specific queries
belong in domain repositories.

## 26. Service Layer

Services (e.g. `MarketService`) orchestrate: request data from a provider,
validate business conditions, call repositories, coordinate transformations,
return domain results. Services are not HTTP-aware and should generally be
callable independently of DRF views.

## 27. API Layer

APIView/DRF endpoints handle: HTTP requests, authentication, permissions,
input validation, serializer invocation, calling services, HTTP responses.
Views stay thin — no major market-analysis algorithms or direct broker
integration in a view.

## 28. Provider Pattern

External systems isolated behind providers (`MockProvider`,
`ZerodhaProvider`). Mock provider: development, tests, UI work, offline
work. Zerodha provider: actual broker/market functionality. Consumers
depend on the provider contract, not the provider-specific implementation.

## 29. Repository Root

```
athena-ai-trading-platform/
    .github/
    backend/
    docker/
    docs/
    frontend/
    scripts/
    tests/
```

Existing structure takes precedence over any proposed architecture diagram.

## 30. Current Django Applications

`accounts`, `dashboard`, `market_data`, `ai_engine`, `paper_trading`,
`backtesting`, `journal`, `knowledge`, `strategies`, `notifications`

Confirm a capability doesn't belong to one of these before creating a new app.
