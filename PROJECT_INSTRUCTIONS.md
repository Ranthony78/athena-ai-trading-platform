# ATHENA — AI ASSISTANT PROJECT INSTRUCTIONS

**Applies to:** every developer and every AI coding assistant (Claude Projects,
Claude Code, or otherwise) working on the Athena AI Trading Platform.

---

## Required Reading Before Modifying Athena

1. `00-QUICK_RECAP.md` — one-page orientation: what Athena is, why, current phase
2. `01-ATHENA_APPLICATION_CONTEXT.md` — full product vision, capabilities, architecture
3. `02-CURRENT_IMPLEMENTATION.md` — what is **actually built** right now, vs. planned
4. `03-AI_LEARNING_FEEDBACK_SYSTEM.md` — design for the prediction/outcome learning loop (read when touching `ai_engine`, `journal`, `backtesting`, or `knowledge`)
5. Relevant module documentation in `docs/`, if present

**The current source code is always the final source of truth**, above every file
listed here. These documents describe intent and status as of their last update —
they do not replace inspecting the actual repository.

---

## Before Creating Any Model, Class, Function, Repository, Service, Serializer, Provider, API, or Utility

- Search the existing codebase first.
- Never duplicate existing functionality.
- Extend working logic rather than replacing it.
- Preserve existing naming conventions.
- Do not redesign the architecture unless explicitly requested.
- Distinguish **IMPLEMENTED**, **PARTIAL**, and **PLANNED** functionality — never
  treat proposed architecture (this document set) as existing code.
- Do not generate speculative files just because they appear in an architecture
  diagram. The repository on disk is authoritative.

---

## Critical Development Rules

1. **Inspect before creating** — never create a model/serializer/repository/service/provider/utility/function/class without checking whether equivalent functionality already exists.
2. **Never duplicate** — a different filename or location is not grounds for a parallel implementation.
3. **Extend existing logic** — working code should normally be extended, not replaced.
4. **Preserve naming conventions** already established in the codebase.
5. **Preserve the architecture** — follow API → Service → Repository → ORM wherever it has been adopted.
6. **Keep views thin** — no major business logic or direct broker integration inside API views.
7. **Keep repositories focused** — persistence only; a repository never decides whether a trade should be entered.
8. **Keep services focused** — orchestration only; don't let a service become a generic dumping ground.
9. **Isolate external providers** — Zerodha-specific (or any broker/LLM-specific) logic belongs behind a provider/integration boundary.
10. **AI must not fabricate market data** — current market values must come from tools/providers, never be invented.
11. **Preserve working code** — don't rewrite an entire working file to add one feature unless a refactor has been explicitly approved.
12. **Check migrations** — every database model change requires migration awareness.
13. **Security first** — never hardcode API secrets, broker credentials, access tokens, database passwords, or Django secret keys; use environment configuration.
14. **Maintain backward compatibility** — existing APIs are not silently changed; breaking changes require explicit approval.
15. **Tests matter** — new business-critical functionality needs tests; trading calculations require deterministic test cases.

---

## Rules Specific to AI Coding Assistants

Before generating code, determine:

1. What already exists?
2. Which module owns the feature?
3. Which architectural layer should change?
4. Is a model change actually necessary?
5. Is there already a repository method for this?
6. Is there already a service method for this?
7. Will the change break an existing API?
8. Are migrations required?
9. Are tests required?
10. Does documentation need updating?

Do not generate dozens of speculative files simply because they appear in an
ideal architecture diagram. The actual repository is authoritative.

---

## Human vs AI Responsibility Boundary

**Application code is responsible for:**
data integrity, calculations, authentication, permissions, orders, positions,
P&L, strategy rules, deterministic indicators, database operations.

**AI is responsible for:**
interpretation, explanation, contextual analysis, scenario generation,
summarisation, probability-oriented reasoning.

This boundary matters for reliability — the AI layer interprets structured
information, it does not generate the underlying facts.

---

## Source-of-Truth Priority (when information conflicts)

1. Current source code
2. Current database models/migrations
3. Current configuration
4. Current tests
5. Current API behaviour
6. Approved project documentation
7. Sprint plans
8. Historical conversation
9. Proposed future architecture (including this document set)

A historical AI conversation — including any past chat with an assistant —
must never override the current codebase.

---

## Existing Django Applications — Do Not Create Duplicates

`accounts`, `dashboard`, `market_data`, `ai_engine`, `paper_trading`,
`backtesting`, `journal`, `knowledge`, `strategies`, `notifications`

Before creating another Django application (including a `learning` app —
see `03-AI_LEARNING_FEEDBACK_SYSTEM.md` §26), confirm the capability doesn't
already belong to one of these.

**Repository root** (do not restructure without explicit approval):

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

---

## Development Safety

- Prefer mock providers where appropriate during development.
- Use paper trading before any live execution.
- Avoid accidental broker order placement.
- Separate development and production configuration.
- Never commit secrets.
- Validate environment configuration before enabling live functionality.

## Observability

Maintain visibility into: API errors, provider errors, authentication
failures, broker failures, market-data failures, AI requests, AI response
failures, background task failures, trading events. Sensitive information
must never be written into logs.

## Documentation Role

`docs/` is the long-term engineering reference and should eventually cover:
project vision, architecture, database, APIs, Django standards, React
standards, AI integration, Zerodha/MCP, coding standards, git workflow,
testing, deployment, security, logging, error handling, prompt engineering,
sprint roadmap. Documentation should describe actual implementation
separately from future architecture.
