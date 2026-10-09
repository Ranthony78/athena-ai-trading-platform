# Athena AI Trading Platform

> **Personal research & development project. Under active development.**
> Not a commercial product. Not financial advice. No live-trading or performance claims are made.

Athena is a personal project to build an AI-assisted market analysis and trading research platform for Indian markets (initial focus: NIFTY, BANK NIFTY and index options). The goal is to bring market data, technical analysis, options analysis, risk analysis and AI interpretation into one platform, built as a maintainable system rather than a collection of scripts.

## Design principles

- **AI is an interpretation layer, never the source of market truth.** Prices come from market-data providers, indicators from deterministic calculations, and positions from the broker or trading engine.
- Analysis should be evidence-based, explainable, auditable and risk-aware.
- Broker integration sits behind a provider abstraction so the architecture is not tied to a single broker.

## Current status

| Area | Status |
|---|---|
| Authentication and initial API infrastructure | Implemented |
| Market-data architecture | In active development |
| Repository layer (instruments, quotes, candles) | Next backend work |
| AI engine, strategy engine | Not yet built |
| Paper trading, backtesting | Not yet built |
| Live broker execution | Not built. No live trading is performed. |

See 02-CURRENT_IMPLEMENTATION.md for the authoritative status.

## Tech stack

Python backend, a separate frontend, Docker Compose for local development, and linting / pre-commit tooling. See requirements.txt and pyproject.toml.

## Documentation

- 00-QUICK_RECAP.md: short overview
- 01-ATHENA_APPLICATION_CONTEXT.md: product vision and intended modules
- 02-CURRENT_IMPLEMENTATION.md: what is implemented today
- 03-AI_LEARNING_FEEDBACK_SYSTEM.md: prediction / outcome learning design

## Disclaimer

This repository is for research and education. Nothing here is investment advice, and nothing here has been validated for live trading. Trading derivatives involves substantial risk of loss.
