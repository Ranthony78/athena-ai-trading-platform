# 03 — AI LEARNING, FEEDBACK & CONTINUOUS IMPROVEMENT

**Status: ⬜ PLANNED** — none of this is built yet (see
`02-CURRENT_IMPLEMENTATION.md`). This is the design spec to build toward once
`ai_engine`, `journal`, `backtesting`, and `knowledge` exist and have real
data flowing through them.

Athena must be designed to learn from historical predictions, trading
decisions, paper trades, backtests, market outcomes, and user feedback.
**"Learning" does not mean the underlying LLM re-trains itself after every
prediction or trade.** Instead, Athena implements a controlled, measurable,
auditable learning system around the AI Engine, answering:

> What did Athena predict, what actually happened, why was the prediction
> correct or incorrect, and what evidence can improve future decisions?

---

## 1. Core Learning Principle

Every sufficiently important analysis has two sides: the **prediction**
(what Athena believed would happen) and the **outcome** (what actually
happened). Athena preserves enough information to compare the two.

```
Market Context → Technical Indicators → Options Data → Strategy Signals →
News/Sentiment → AI Analysis → Prediction → Confidence → Trade/No-Trade →
Actual Market Outcome → Evaluation → Mistake/Success Classification →
Historical Learning Record → Future Context Retrieval
```

## 2. What Athena Should Record

A structured snapshot of everything available at decision time:

Instrument, exchange, timestamp, trading session, current price, previous
close, open/high/low/volume, market regime, relevant candle history, support
levels, resistance levels, VWAP, EMA values, RSI, MACD, ATR, ADX, other
indicators, option-chain info, PCR, OI, change in OI, IV, market breadth,
volatility info, news sentiment, strategy signals, existing positions, risk
conditions, AI model/provider, prompt version, AI response, bullish/bearish/
sideways probability, confidence score, suggested entry/stop/target,
trade/no-trade decision.

**This snapshot must reflect only what was known at prediction time** —
Athena evaluates predictions using that snapshot, never reconstructed with
future information. This prevents look-ahead bias.

## 3. Outcome Recording

After an appropriate evaluation period, record: price after prediction,
maximum favourable/adverse excursion, target reached / stop reached /
neither, time to target, time to stop, end-of-session price, actual
direction, actual volatility, trade P&L, risk/reward achieved.

## 4. Prediction Evaluation

Evaluate programmatically wherever possible, and go beyond WIN/LOSS.
Example:

```
Prediction: Direction Bullish, Confidence 78%, Entry 56,200, Target 56,600, Stop 56,000
Outcome:    Entry triggered, Stop reached, Target not reached
```

Richer classification examples: direction correct but entry poor; direction
correct but target unrealistic; direction correct but stop too tight;
direction incorrect; direction correct but timing incorrect; high-confidence
false signal; low-confidence correct signal; no-trade recommendation
correctly avoided poor conditions; strategy signal correct but AI
interpretation incorrect; AI interpretation correct but execution logic poor.

## 5. Mistake Classification

- **Direction Error** — expected bullish, market went bearish (or vice versa)
- **Timing Error** — expected move happened, outside the predicted window
- **Entry Error** — direction correct, entry poor
- **Stop-Loss Error** — thesis eventually correct, stop unnecessarily tight
- **Target Error** — direction correct, target unrealistic
- **Confidence Error** — excessive confidence on an incorrect prediction
- **Regime Classification Error** — trending/ranging/volatile/low-vol misread
- **Indicator Interpretation Error** — values correct, interpretation poor
- **Options Interpretation Error** — option-chain evidence misread
- **News/Sentiment Error** — inappropriate weight given to news/sentiment
- **Data Quality Error** — based on stale/incomplete/incorrect data
- **Execution Error** — analysis valid, sim/real execution produced the failure

A losing trade does not automatically mean the underlying analysis was wrong
— these categories separate the two.

## 6. Success Classification

Identify which evidence contributed to a good outcome: trend + VWAP
alignment, EMA alignment, strong ADX trend, option-chain confirmation, OI
confirmation, market breadth confirmation, momentum confirmation, news
confirmation, multi-timeframe confirmation, correct volatility regime,
successful support/resistance reaction. The goal is to find which
combinations repeatedly work, not just what failed.

## 7. Confidence Calibration

AI confidence must be measured against actual historical accuracy. Example:
100 predictions at 80–90% confidence, only 58% correct → systematically
overconfident. Athena should maintain calibration stats across ranges:

| Confidence Range | Actual Accuracy |
|---|---|
| 50–59% | 53% |
| 60–69% | 62% |
| 70–79% | 68% |
| 80–89% | 74% |
| 90–100% | 79% |

Goal: a well-calibrated 70% prediction succeeds ~70% of the time, not that
confidence numbers merely *look* impressive.

## 8. Market-Regime Learning

Performance should eventually be measured by regime: strong bullish trend,
strong bearish trend, sideways, high/low volatility, gap-up/gap-down
session, expiry session, event-driven session. A strategy may perform well
in strong trends but poorly in low-vol consolidation — future analysis
incorporates this.

## 9. Strategy-Specific Learning

Every strategy (ORB, VWAP, EMA crossover, momentum, breakout, mean
reversion, options buying/selling, ...) maintains its own performance
history: number of signals/trades, win/loss rate, average return, average
winner/loser, max drawdown, expectancy, profit factor, and performance
segmented by instrument, timeframe, regime, and time of day. Use sufficient
observations before drawing conclusions.

## 10. Time-of-Day Learning

Measure performance across windows: open, early morning, mid-morning,
midday, afternoon, final hour — intraday behaviour and strategy/AI
performance can vary significantly by window.

## 11. Instrument-Specific Learning

Don't assume a pattern found in BANK NIFTY transfers identically to another
instrument. Segment stats by instrument, instrument type, exchange, sector,
index, futures, options, expiry.

## 12. Three Levels of Athena Learning

**Level 1 — Memory Learning.** Store previous analyses, predictions,
outcomes, mistakes, successful patterns, lessons, trade history. Retrieve
relevant historical cases as AI context. Does not modify the LLM.

**Level 2 — Statistical Learning.** Deterministic, app-layer calculation of
strategy win rates, confidence calibration, performance by regime/
instrument/timeframe, indicator combinations, drawdowns, expectancy. Never
delegate core statistics to the LLM.

**Level 3 — Model Learning** *(later stage)*. Train/fine-tune dedicated ML
models — direction classification, regime classification, volatility
forecasting, signal ranking, trade-quality scoring, probability estimation —
only once sufficient clean, labelled, validated data exists.

## 13. Learning Memory

A structured Learning Record, not just free-text notes:

```
Learning Record
    Analysis ID, Instrument, Timestamp, Market Regime, Strategy,
    Prediction, Confidence, Evidence, Outcome, Error Classification,
    Performance, Lesson, Validation Status
```

Structured so records can be queried and statistically analysed.

## 14. Similar Historical Case Retrieval

Before a new AI analysis, retrieve comparable historical situations. Example:

```
Current: BANK NIFTY, High volatility, Above VWAP, RSI 68, Bullish EMA
structure, Weak market breadth, Bearish options OI

Retrieved: Similar setup count 47 — Bullish outcome 19, Bearish 24, Sideways 4
```

This can improve current-analysis quality — but historical similarity is
never presented as certainty.

## 15. No Look-Ahead Bias — MANDATORY

Athena must never use future market information when evaluating what was
knowable at decision time. Backtesting, strategy evaluation, and
AI-learning datasets must preserve the boundary between information
available at decision time vs. observed afterward. Violating this produces
misleadingly high performance.

## 16. No Autonomous Self-Rewriting

Athena must NOT automatically rewrite production strategies because of
individual wins/losses. One lost trade must never automatically trigger
"change the strategy" — markets contain randomness, and valid strategies
naturally lose sometimes. Changes require sufficient evidence.

## 17. Controlled Improvement Process

```
Prediction → Observation → Outcome Measurement → Error Classification →
Historical Aggregation → Pattern Detection → Improvement Hypothesis →
Backtest → Out-of-Sample Validation → Paper Trading →
Performance Comparison → Human Approval → Production Promotion
```

This protects Athena from "learning" incorrect rules from random
short-term market noise.

## 18. Human Approval

Required for material production changes: strategy parameter changes,
risk-rule changes, position-sizing changes, stop-loss policy changes,
broker execution changes, AI prompt changes affecting trading decisions,
new production strategies. **Athena may recommend improvements — it must
not silently promote them.**

## 19. Backtesting Integration

Improvement hypotheses discovered by the learning system get validated
through Backtesting. Example: "High-confidence bullish predictions perform
poorly when market breadth is strongly negative" → hypothesis "reduce
bullish signal strength when breadth is strongly negative" → backtest it.
Only statistically meaningful improvements proceed further.

## 20. Paper-Trading Validation

A successful backtest alone is not sufficient. Sequence:

```
Historical Analysis → Backtest → Out-of-Sample Test → Paper Trading →
Production Consideration
```

## 21. Prompt Learning

Prompts are version controlled (`banknifty_analysis_v1`, `_v2`, `_v3`, ...).
Every prediction records the prompt version used, so prompt changes are
measurable rather than subjective.

## 22. Model Comparison

If multiple AI providers/models are supported, measure performance per
model (direction accuracy, calibration error, average latency) so provider
selection can be evidence-based, not preference-based.

## 23. Data Quality

Never treat incomplete, corrupted, stale, or misaligned market data as
trustworthy learning evidence. Track data-quality flags: missing candles,
stale quote, missing option chain, delayed provider response, missing OI,
missing news, incomplete indicator history. Poor-quality observations may
need exclusion from statistical learning.

## 24. Explainability

The learning system stays auditable. Prefer:

> "Bullish confidence was reduced because historically similar setups with
> negative market breadth and bearish OI showed weak bullish follow-through."

over an unexplained `AI confidence = 61%`.

## 25. Learning Safety Rules (mandatory)

1. AI must never fabricate historical outcomes.
2. Market outcomes must come from actual stored/provider data.
3. Statistical calculations must be deterministic.
4. Future information must not leak into historical predictions.
5. One losing trade must not redefine a strategy.
6. One winning trade must not validate a strategy.
7. Strategy changes require sufficient evidence.
8. Important changes must be backtested.
9. Production-impacting changes require approval.
10. Learning history must remain auditable.
11. Prompt versions must be traceable.
12. Model/provider versions must be traceable.
13. Poor-quality data must not silently become learning evidence.
14. AI-generated lessons must be distinguishable from measured facts.
15. Risk controls must override AI recommendations.

## 26. Relationship With Existing Athena Modules

**Do not automatically create a new Django app called `learning`.** Build
this capability inside existing modules:

| Module | Responsible for |
|---|---|
| `ai_engine` | Predictions, AI reasoning, confidence, prompt versions, model/provider info |
| `journal` | Trade outcomes, observations, user notes, mistakes, lessons |
| `backtesting` | Hypothesis testing, historical validation, strategy comparison |
| `knowledge` | Reusable lessons, historical context, relevant knowledge retrieval |
| `strategies` | Deterministic trading rules, strategy definitions, strategy versions |
| `market_data` | Objective market history used for evaluation |

Only create a dedicated `learning` app later if these boundaries prove
insufficient.

## 27. Long-Term Objective

Athena evolves from *"AI that analyses the market"* → *"AI-assisted trading
intelligence that measures the quality of its own historical decisions"* →
eventually *"a controlled adaptive trading research platform that can
identify, validate, and recommend improvements using accumulated evidence."*
The objective is measurable continuous improvement — **not** uncontrolled
autonomous self-modification.

## 28. Core Requirement (permanent product requirement)

> Athena must be capable of learning from historical predictions and
> trading outcomes. Learning must be evidence-based, measurable,
> reproducible where possible, and auditable. The system must record
> predictions, relevant market context, confidence, actual outcomes, errors
> and lessons. Historical evidence may influence future AI analysis, but
> the AI must not autonomously modify production trading rules or
> mandatory risk controls. Material improvements must be validated through
> sufficient historical evidence, backtesting, forward/paper-trading
> validation, and human approval before production promotion.
