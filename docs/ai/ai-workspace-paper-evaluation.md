# AI Workspace and paper evaluation

## Request record

Each saved `AnalysisSession` retains the exact system and user prompt, evidence snapshot, configured provider/model, prompt version, and SHA-256 digest. Provider failures retain the request for diagnosis. Prompt preview and request history expose this data only to the signed-in session owner.

The prompt preview labels whether an active database template was used or the built-in versioned fallback was used. On 2026-09-30, the configured checkout's SQLite database contained no `MARKET_ANALYSIS` prompt-template rows, so its effective system prompt was the built-in default plus the runtime Athena contract. This database observation is environment-specific and should be rechecked after prompt administration changes.

Gemini/Kimi selection remains in the provider factory. The prompt requires structured market view and scenarios, evidence for and against, invalidation conditions, missing inputs, and an explicit No Trade reason. Athena’s empirical horizon probabilities are inserted unchanged. The AI confidence is a separate qualitative field. Historical excursion ranges and support/resistance are calculated from supplied market data; option delta is sensitivity, not odds of profit. The raw prose is retained separately from the normalized display fields.

## Evidence limits

The supplied Claude HTML is a static presentation reference, not a market-data source. Its sample prices, dates, flow figures and probabilities are not imported into Athena. Its white/navy/indigo styling is available as the additive Ivory & Indigo theme, with the supplied font stored locally; other themes remain selectable.

`athena-workspace-v5` and `athena-evidence-v3` add a p9-inspired ATM option-buying input audit. Valid bid/ask pairs supply combined mid and ask debit references. IV velocity history, OI deltas, five-day gamma history and opening spread comparisons remain unavailable until corresponding observations exist. The p9 IV-velocity/theta comparison mixes units and is labelled INVALID_UNITS, not a failed market filter. Expiry premium breakeven does not establish intraday expectancy. The audit does not generate edge scores, option win rates or regime/IV-crush probabilities and does not change trading gates. Saved requests retain their original evidence/version.

The `athena-evidence-v2` packet adds an experimental daily movement comparison inspired by `algo_ai`: VIX daily one-sigma points, mean absolute open-to-close movement over the latest 15 completed verified Zerodha sessions, and their equal-weight blend. All 15 sessions must have valid positive open and close prices; missing sessions suppress the blend. Both inputs and sample count appear in the workspace. Mean absolute movement and standard deviation are different statistics, so this descriptive blend is uncalibrated and does not alter intraday horizon estimates, empirical probabilities, paper eligibility, or order rules. Old saved requests remain readable without this field.

The source panel groups linked, dated Marketaux headlines into broad driver topics. Headlines from the prior 24 hours with source and URL are marked usable. An empty topic means that feed did not provide usable coverage; it does not mean no event or risk exists. Read-only Zerodha quotes can supply the nearest unexpired MCX crude-oil and CDS USD/INR futures when those contracts are imported; the card shows contract expiry and excludes quotes older than five minutes or without a timestamp. These futures are not spot prices. The current configured instrument catalog had no active crude or USD/INR contracts, so those quote rows remain unavailable until instruments are refreshed. No verified global-index price feed or scheduled-event calendar is connected; both are explicitly labeled unavailable. No headline is treated as an instruction to the model.

The prompt preview and saved request view expose the exact prompt, provider/model, version, evidence timestamp, and source packet. After an analysis, the page opens the exact captured request instead of silently replacing it with a newer preview.

Resolved observations are user scoped and are appended to later prompts as retrospective counts. They do not change probabilities or rules. The calibration candidate uses non-overlapping observations from `horizon-base-rate-v1`, an earlier training segment, and a later holdout; it never promotes itself.

## Paper evaluation

Paper evaluation is an explicit checkbox on the AI Analysis page, checked by default. A qualifying saved live-session BUY/SELL with a fresh Zerodha price, active suggested NFO option, future evaluation horizon, and recent worker heartbeat may create a one-lot **paper** long-option entry. `NO_SETUP`/`NEUTRAL`/`WATCH` is displayed as No Trade and never creates a position.

The simulator records its version and assumptions: 10 basis points of adverse slippage per fill, ₹20 brokerage per fill, and taxes excluded. Positions are exited on the first fresh quote available at/after the requested horizon. If market access is unavailable at that time, the evaluation remains waiting and reports the delay; it does not backdate a fill. Expired contracts requiring settlement remain for review rather than receiving a fabricated settlement price. The existing user-authored journal summary is not changed; a linked per-trade note records completed paper outcomes.

No live-order endpoint is called by this workflow. Live order settings and theme configuration are outside this feature.

## Worker and verification

Celery Beat calls the outcome task every minute. To run an independent local worker from the project root, use:

```powershell
& '.\.venv\Scripts\python.exe' backend/manage.py run_learning_worker
```

The worker only refreshes needed one-minute market candles, resolves price forecasts, and manages simulated paper exits. It does not call an AI provider or broker order API. The `/api/ai/learning/` response shows whether its database heartbeat is recent.

An additive SQLite backup was saved to `backend/backups/before_workspace_learning_20260930.sqlite3` before migration `ai_engine.0005_workspace_learning_audit` was applied. A zero/low sample report is expected until live forecasts have matured and paper trades have closed. No market data is generated by an AI or mock provider for automated option paper fills.
