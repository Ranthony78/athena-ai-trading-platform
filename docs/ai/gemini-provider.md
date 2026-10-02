# Gemini AI Provider

Users can connect a personal Gemini key from **Settings → AI Connection**.
Athena encrypts the key before storing it and never returns it to the browser.
An authenticated user can also choose Kimi, Claude, or Groq; the saved personal
provider takes precedence over server configuration for that user's analyses.

For a shared server-level configuration, set `AI_PROVIDER` and its matching
provider key in the backend environment. `GEMINI_MODEL` can select a model
enabled for that Google AI project; the default is `gemini-3.5-flash`. Restart
the backend after changing server-level settings.

Credential encryption is derived from `DJANGO_SECRET_KEY`. Set a unique,
high-entropy Django secret of at least 32 characters before saving user keys.
Rotating that secret makes previously saved AI keys unreadable, so users must
save their provider keys again afterward.

The provider uses Athena's existing prompt and analysis pipeline. It does not
change the market evidence supplied to the model, the output schema, strategy
behavior, broker permissions, or order execution. Claude-named model values in
existing prompt templates are mapped to `GEMINI_MODEL`; explicitly configured
Gemini model identifiers are passed through.

Provider failures are reported without logging or returning API keys or raw
provider response bodies. A bad `AI_PROVIDER` value raises a configuration
error instead of silently selecting mock AI.
