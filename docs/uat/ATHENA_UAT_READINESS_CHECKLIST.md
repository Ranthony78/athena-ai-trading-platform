# Athena UAT Readiness Checklist

Status values: Not run / Pass / Fail / Blocked. Record build/commit, environment, tester, date, screenshots/log references, and defect ID for each failed or blocked item. Use a dedicated UAT database and paper-only broker configuration. Never use production credentials or submit live orders during this checklist.

## Release gates

- [ ] Development and UAT settings both force `LIVE_TRADING_ENABLED=False`; confirm no live order can be placed even if the UI is manipulated.
- [ ] Production is not considered ready while production settings default live trading on, unless separately changed and protected by reviewed account-level authorization, spending/quantity limits, kill switch, and audit logging.
- [ ] Secrets are unique and supplied through environment/secret storage; no default Django secret, broker token, or AI key is committed or written to logs.
- [ ] Restricted CORS origins, HTTPS, secure session/CSRF cookies, backups, database and worker configuration are verified for the intended deployment.
- [ ] Backend automated tests, migrations, frontend build, lint/static checks, and browser smoke tests pass in a reproducible environment. Record failures; do not mark blocked checks as passed.
- [ ] Paid AI API is not required to test deterministic data, paper trading, or UI behavior. Start paid-provider UAT only after the above safety and functional gates pass; set a small spend cap and usage alerts first.

## 1. Access, accounts, and settings

- [ ] Login succeeds with valid credentials; invalid credentials show a clear error and do not expose internals.
- [ ] Signup, Google login (when configured), logout, password reset, expired access token, refresh, and revoked/disabled user flows work end to end.
- [ ] Email-verification policy is enforced as intended; auth endpoints have sensible throttling.
- [ ] Regular user cannot open user management; administrator can list users, deactivate/reactivate, and trigger the documented password-reset flow.
- [ ] Profile/settings persist after reload. Theme, density, and responsive layouts remain readable in every supported theme.
- [ ] AI provider keys can be created, masked, tested, replaced, and removed; failed provider connection does not break non-AI pages. Confirm spend/usage reporting and provider fallback behavior.

## 2. Dashboard and market data

- [ ] Dashboard loads with market open, market closed, provider disconnected, empty data, and provider error. Missing data is shown as unavailable, not as a fabricated zero or stale live value.
- [ ] NIFTY/Bank NIFTY quote, change, OHLC, timestamp, session status, and chart interval agree with the verified source.
- [ ] Chart handles refresh, interval changes, resize, zoom, no candles, stale candles, and network interruption without freezing or silently relabeling data.
- [ ] Market Watch/Historical show source, timestamp/timezone, selected interval and date range correctly; no look-ahead leakage in historical views.
- [ ] Option chain expiry, ATM strike, CE/PE, bid/ask, LTP, volume/OI, Greeks, lot size, and stale/empty-chain behavior match the broker feed. Check expiry-day and holiday boundaries.
- [ ] Pivot/CPR, support/resistance, multi-timeframe trend, RSI/EMA/VWAP, VIX move, and opening-range values are reproducible from the displayed source candles. Verify rounding, timeframe alignment, and IST day boundaries.
- [ ] Provider throttling, partial quote responses, token expiry, and reconnect are handled with visible status and safe retry behavior.

## 3. Athena analysis workspace

- [ ] Each market, candle interval, forecast horizon, and mode selection changes the request as labeled and clears stale results appropriately.
- [ ] Preview input contains only sourced fields and clearly marks unavailable evidence; no guessed session state, news, or macro coverage.
- [ ] Run analysis with a configured provider, unavailable provider, malformed response, timeout, missing market data, closed market, and high-event-risk evidence.
- [ ] Validate output schema: market view, scenarios, no-trade reason, evidence/conflicts, invalidation, missing information, and citations are present and accurately rendered.
- [ ] NO_SETUP/NEUTRAL/WATCH are shown as No Trade with concrete reasons. Historical probabilities remain distinct from AI confidence and are never invented or adjusted by the model.
- [ ] Headlines, trader notes, and historical lessons cannot override system rules. Supplied source links open the exact source and are not fabricated.
- [ ] Analysis history saves, reloads, filters, and deletes only the current user's records; refresh does not duplicate or corrupt sessions.
- [ ] Network retry/double-click cannot create duplicate analyses or duplicate paper positions. Record provider, model, latency, tokens/cost where available.

## 4. Candidate options and experimental BOTH setup (paper only)

- [ ] Directional CE/PE recommendation uses the correct underlying, direction, expiry, strike, contract token, lot size, quote timestamp, and order side; no recommendation appears when evidence is insufficient.
- [ ] BOTH is clearly labeled experimental and paper-only; its rationale, gates, combined ask debit, estimated costs, max premium loss, unknown event-calendar status, and limitations are visible.
- [ ] Gate rejects mock/unverified/stale data, mismatched horizon, mismatched strike/expiry/lot size, missing/crossed bid/ask, excessive spread, insufficient volatility hurdle, and explicit high-event-risk evidence.
- [ ] Test every failure boundary (exact staleness threshold, spread limit, relative-volatility threshold, premium hurdle); verify a missing field fails closed.
- [ ] A passing pair opens exactly one CE and one PE paper leg atomically. Force either leg to fail and confirm both orders/positions roll back.
- [ ] Paper fills use option ask to buy and bid to sell plus slippage. Inspect fees, quantities, combined debit, aggregate P&L, and max-loss display against hand calculations.
- [ ] At horizon, both legs exit; simulate one failed exit, worker restart, market closed, stale quote, and expired contract. Partial state is visible/retried; unresolved expiry is flagged for review without invented settlement prices.
- [ ] Confirm candidate and pair outcomes do not create duplicate calibration samples; incomplete pair is excluded and a complete pair counts as one strategy outcome.
- [ ] Save a paper-forward test record for every evaluated candidate, including ineligible candidates and the reason. Do not tune thresholds from a tiny sample.

## 5. Paper trading and order lifecycle

- [ ] Manual paper market/limit orders validate buying power, quantity/lot multiples, side, instrument, price, and user ownership.
- [ ] Reject insufficient funds, invalid instrument, stale quotes, duplicate submission, invalid limit, and unauthorized cross-user access with understandable messages.
- [ ] Verify order states from submission through fill/reject/cancel; reconcile order, position, trade, fees, and portfolio totals after refresh.
- [ ] Verify partial fills, cancellation races, market close, and broker/data outage. No paper failure can fall through to the live broker.
- [ ] Portfolio, Orders, Positions, Trades, and dashboard totals agree from the same underlying records.

## 6. Zerodha integration (read-only in UAT)

- [ ] Connect/disconnect/reconnect and token expiry behavior are clear; tokens never appear in page source, API responses, browser logs, or server logs.
- [ ] Funds, positions, and order history are read-only and reconcile to the broker. Test permission denial and disconnected account.
- [ ] Keep live order creation disabled throughout UAT; verify server-side denial directly, not only hidden/disabled UI controls.

## 7. Strategies, backtesting, and research

- [ ] Strategy create/edit/enable/disable and signal ownership/permissions work; signals disclose timeframe, input data, and timestamps.
- [ ] Backtest rejects invalid ranges/parameters; verify fees, slippage, lot sizing, no future-data leakage, drawdown, trade count, and reproducibility with a fixed dataset.
- [ ] Compare at least one small result manually against source candles and hand-calculated trades before trusting aggregate metrics.
- [ ] Knowledge articles/rules/prompts and AI lessons are permission-checked; stored user notes remain untrusted evidence and cannot silently change production rules.

## 8. Journal, notifications, and user management

- [ ] Journal create/edit/delete, daily uniqueness, P&L totals, lessons, and AI review persist and remain user-scoped.
- [ ] Alerts trigger once under the intended conditions, respect expiry/repeat settings, and recover from unavailable email/Telegram delivery.
- [ ] Notification preferences and read/unread state persist; failed delivery is visible and does not lose the alert.
- [ ] User-management operations are administrator-only, logged, reversible where intended, and cannot deactivate the current sole administrator accidentally.

## 9. UX, accessibility, and operations

- [ ] Test desktop, tablet, and mobile widths; keyboard-only navigation; visible focus; labels/errors; contrast; chart descriptions; and long/empty/loading/error states.
- [ ] Verify navigation routes, browser back/forward, deep links, 404 fallback, and session timeout. No page is blank on a recoverable API error.
- [ ] Check console/network for uncaught errors, leaked credentials, repeated polling, excessive payloads, and duplicate requests.
- [ ] Measure first load and chart/analysis response times on a realistic connection. Track bundle size and confirm long-poll/refresh does not overwhelm the API.
- [ ] Confirm logs identify request/user/session safely, redact secrets, and support investigation of analysis and paper-order decisions.
- [ ] Verify database backup/restore, migration from the current SQLite UAT data, retention/deletion behavior, and a tested recovery procedure.

## Paid AI API purchase decision

Do not buy a production-sized plan just to begin UAT. First complete access, data, analysis-schema, paper-safety, and server-side live-order-denial checks using mock/free/low-cost options where available. Then connect one provider with a hard monthly cap and usage alerts. Compare it on a fixed, versioned set of representative market snapshots: schema validity, unsupported claims, no-trade behavior, source handling, latency, token cost, and reproducibility. A paid model must not supply prices, probabilities, or missing data; Athena's deterministic data and risk gates remain authoritative.

Purchase/continue only if: (1) the actual provider key is stored securely server-side, (2) per-request usage and cost can be monitored, (3) UAT cases pass without relaxing safety rules, and (4) expected monthly usage is affordable at the observed token rate. Recheck provider terms, data privacy, retention, and current pricing before subscribing.

## UAT sign-off

- Build/commit:
- Environment and data source:
- Tester/date:
- Passed / failed / blocked totals:
- Open critical/high defects:
- Paid API provider and monthly cap (if used):
- Live trading confirmed disabled by server-side test:
- UAT decision: Go / No-Go / Go with listed limits:
- Approver:
