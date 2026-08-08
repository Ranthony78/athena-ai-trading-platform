# 00 — QUICK RECAP: ATHENA AI TRADING PLATFORM

## What Athena Is

Athena is an AI-assisted market analysis, trading research, strategy
development, paper-trading, and backtesting platform — not just a price
viewer or indicator display. It combines live market data, historical
market data, technical analysis, options analysis, trading strategies, AI
interpretation, news/sentiment, risk analysis, paper trading, backtesting,
journaling, knowledge management, and broker integration into a single
platform.

Initial market focus: Indian markets — NIFTY, BANK NIFTY, index derivatives,
futures, options, NSE-listed securities. Initial broker/market integration:
**Zerodha**, behind a provider abstraction so the architecture is never
permanently tied to one broker.

## Why It Exists

Retail trading workflows are normally fragmented across separate tools for
charts, option-chain data, news, technical analysis, AI analysis, and
journaling/backtesting. Athena consolidates these into one platform capable
of collecting market information, analysing it through both deterministic
logic and AI models, presenting probability-based analysis, and supporting
controlled trade execution — as a platform, not a collection of scripts.

## Core Philosophy

AI is an **interpretation layer**, never the source of market truth.

- Market prices → authorised market-data providers
- Indicators → deterministic calculations
- Account balances / positions → broker/trading engine
- AI → interprets the above; never fabricates missing data

Analysis should be evidence-based, probability-based, explainable, auditable,
reproducible where possible, and risk-aware. These stay separated in the
architecture: raw market data → derived indicators → strategy signals → AI
interpretation → risk assessment → trade recommendation → trade execution.

## Current Phase (update this each time the doc set is regenerated)

- Foundation stage — active development.
- Authentication and initial API infrastructure: **operational**.
- Market-data architecture: **under active development**.
- Repository layer (`base_repository.py`, `instrument_repository.py`,
  `quote_repository.py`, `candle_repository.py`): **next major backend work**
  — check the actual repo before assuming these files don't exist yet.
- AI engine, strategy engine, paper trading, backtesting, production broker
  execution: **not yet built** — see `02-CURRENT_IMPLEMENTATION.md` for the
  authoritative status table.

## Where To Go Next

- Full product vision and every module's intended capabilities → `01-ATHENA_APPLICATION_CONTEXT.md`
- What's actually implemented today → `02-CURRENT_IMPLEMENTATION.md`
- The prediction/outcome learning system design → `03-AI_LEARNING_FEEDBACK_SYSTEM.md`
- Rules every assistant must follow before writing code → `PROJECT_INSTRUCTIONS.md`
