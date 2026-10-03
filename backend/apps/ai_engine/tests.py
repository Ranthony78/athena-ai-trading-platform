from datetime import datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

import httpx
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.ai_engine.api.serializers import AnalysisRequestSerializer
from apps.ai_engine.api.views import AnalysisSessionListAPIView
from apps.ai_engine.models import AnalysisSession
from apps.ai_engine.providers.gemini_provider import GeminiProvider
from apps.ai_engine.services.confidence_calibration_service import (
    ConfidenceCalibrationService,
)
from apps.ai_engine.services.forecast_outcome_service import ForecastOutcomeService
from apps.ai_engine.services.output_validator import OutputValidator
from apps.market_data.models import Candle, Instrument


class HistoricalProbabilityValidationTests(SimpleTestCase):
    def test_model_percentages_are_cleared_when_empirical_base_is_unavailable(self):
        parsed = {
            "probability": {
                "upside_pct": 81,
                "downside_pct": 9,
                "sideways_pct": 10,
            }
        }

        warning = OutputValidator._enforce_historical_probability(parsed, {})

        self.assertIsNone(warning)
        self.assertIsNone(parsed["probability"]["upside_pct"])
        self.assertIsNone(parsed["probability"]["downside_pct"])
        self.assertIsNone(parsed["probability"]["sideways_pct"])

    def test_empirical_base_replaces_ai_estimate_and_malformed_estimate_is_safe(self):
        parsed = {"probability": {"upside_pct": "not-a-number"}}
        context = {
            "intraday_probability_base_rate": {
                "upside_pct": 50,
                "downside_pct": 30,
                "sideways_pct": 20,
                "sample_size": 40,
                "timeframe": "15m",
                "horizon_minutes": 15,
                "time_of_day_tolerance_minutes": 30,
                "sideways_band_pct": 0.05,
                "low_confidence": True,
            }
        }

        warning = OutputValidator._enforce_historical_probability(parsed, context)

        self.assertIsNotNone(warning)
        self.assertEqual(parsed["probability"]["upside_pct"], 50)
        self.assertEqual(parsed["probability"]["downside_pct"], 30)
        self.assertEqual(parsed["probability"]["sideways_pct"], 20)


class NextSessionAnalysisTests(SimpleTestCase):
    def test_next_session_is_planning_only_and_keeps_ai_market_view(self):
        parsed = {
            "signal": "BUY",
            "market_view": "BULLISH",
            "no_trade_reason": "",
            "scenarios": {
                "bullish": "Break above supplied resistance",
                "bearish": "",
                "sideways": "",
            },
            "confidence": 62,
        }

        result = OutputValidator.validate(
            parsed,
            {"analysis_mode": "NEXT_SESSION"},
            "",
        )["parsed"]

        self.assertEqual(result["signal"], "NO_SETUP")
        self.assertIn("Next-session outlook", result["no_trade_reason"])
        self.assertEqual(result["market_view"], "BULLISH")
        self.assertEqual(
            result["scenarios"]["bullish"], "Break above supplied resistance"
        )

    @patch(
        "apps.paper_trading.services.broker_simulator.BrokerSimulator._quote_is_stale",
        return_value=False,
    )
    def test_closed_live_request_does_not_leak_ai_next_session_scenarios(
        self, _is_stale
    ):
        parsed = {
            "signal": "BUY",
            "market_view": "BULLISH",
            "no_trade_reason": "",
            "scenarios": {
                "bullish": "Tomorrow may rally above resistance",
                "bearish": "Tomorrow may break support",
                "sideways": "Tomorrow may stay in range",
            },
            "confidence": 72,
            "target": 22490,
            "stop_loss": 22390,
        }
        context = {
            "analysis_mode": "LIVE",
            "quote_source": "ZERODHA",
            "quote": {"ltp": 22420, "timestamp": "2026-10-02T09:00:00+05:30"},
            "session": {"is_live": False, "session": "CLOSED", "time": "09:00:00"},
        }

        result = OutputValidator.validate(parsed, context, "")["parsed"]

        self.assertEqual(result["signal"], "NO_SETUP")
        self.assertEqual(result["market_view"], "UNCERTAIN")
        self.assertEqual(result["confidence"], 0)
        self.assertTrue(
            all(
                "select NEXT_SESSION" in value for value in result["scenarios"].values()
            )
        )
        self.assertIsNone(result["target"])
        self.assertIsNone(result["stop_loss"])
        self.assertTrue(
            any(
                "use NEXT_SESSION explicitly" in item
                for item in result["missing_information"]
            )
        )

    def test_next_session_cannot_enable_paper_evaluation(self):
        serializer = AnalysisRequestSerializer(
            data={
                "symbol": "NIFTY",
                "analysis_mode": "NEXT_SESSION",
                "paper_evaluate": True,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("paper_evaluate", serializer.errors)


class AnalysisHistoryClearAPITests(TestCase):
    @patch("apps.ai_engine.models.AnalysisSession.objects.filter")
    def test_clear_history_is_scoped_to_authenticated_user(self, filter_sessions):
        queryset = filter_sessions.return_value
        queryset.count.return_value = 2
        queryset.delete.return_value = (
            5,
            {"ai_engine.AnalysisSession": 2, "ai_engine.AISignal": 3},
        )
        user = type("AuthenticatedUser", (), {"is_authenticated": True, "id": 812})()
        request = APIRequestFactory().delete("/api/ai/sessions/")
        force_authenticate(request, user=user)

        response = AnalysisSessionListAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["sessions_deleted"], 2)
        filter_sessions.assert_called_once_with(user=user)


class GeminiProviderTests(SimpleTestCase):
    @override_settings(GEMINI_API_KEY="test-key", GEMINI_MODEL="gemini-3.8-flash")
    @patch("apps.ai_engine.providers.gemini_provider.httpx.post")
    def test_generate_content_uses_header_key_and_extracts_text(self, mock_post):
        mock_post.return_value = httpx.Response(
            200,
            json={
                "modelVersion": "gemini-3.8-flash",
                "candidates": [{"content": {"parts": [{"text": "market analysis"}]}}],
                "usageMetadata": {"totalTokenCount": 23},
            },
            request=httpx.Request(
                "POST", "https://generativelanguage.googleapis.com/test"
            ),
        )

        result = GeminiProvider().complete(
            "system", "evidence", model="claude-sonnet-4-6"
        )

        call = mock_post.call_args
        # The configured Gemini model is used, not the Claude name from the template,
        # and the key travels in a header, never in the URL.
        self.assertIn("gemini-3.8-flash", call.args[0])
        self.assertNotIn("test-key", call.args[0])
        self.assertEqual(call.kwargs["headers"]["x-goog-api-key"], "test-key")
        self.assertEqual(result["content"], "market analysis")
        self.assertEqual(result["tokens_used"], 23)

    @override_settings(GEMINI_API_KEY="test-key", GEMINI_MODEL="gemini-3.8-flash")
    @patch("apps.ai_engine.providers.gemini_provider.time.sleep")
    @patch("apps.ai_engine.providers.gemini_provider.httpx.post")
    def test_service_unavailable_is_retried_with_backoff_and_safe_error(
        self, mock_post, mock_sleep
    ):
        mock_post.return_value = httpx.Response(
            503,
            json={"error": {"message": "provider busy"}},
            request=httpx.Request(
                "POST", "https://generativelanguage.googleapis.com/test"
            ),
        )

        with self.assertRaisesRegex(Exception, "temporarily unavailable") as ctx:
            GeminiProvider().complete("system", "evidence")

        # Initial attempt plus every configured retry, sleeping between them only.
        self.assertEqual(
            mock_post.call_count, GeminiProvider.MAX_UNAVAILABLE_RETRIES + 1
        )
        self.assertEqual(mock_sleep.call_count, GeminiProvider.MAX_UNAVAILABLE_RETRIES)
        # Raw provider text must not leak into the user-facing error.
        self.assertNotIn("provider busy", str(ctx.exception))

    @override_settings(GEMINI_API_KEY="test-key", GEMINI_MODEL="gemini-3.8-flash")
    @patch("apps.ai_engine.providers.gemini_provider.time.sleep")
    @patch("apps.ai_engine.providers.gemini_provider.httpx.post")
    def test_client_error_is_not_retried(self, mock_post, mock_sleep):
        mock_post.return_value = httpx.Response(
            400,
            json={"error": {"message": "bad request"}},
            request=httpx.Request(
                "POST", "https://generativelanguage.googleapis.com/test"
            ),
        )

        with self.assertRaisesRegex(Exception, "HTTP 400"):
            GeminiProvider().complete("system", "evidence")

        self.assertEqual(mock_post.call_count, 1)
        mock_sleep.assert_not_called()


class ForecastOutcomeTests(TestCase):
    def setUp(self):
        self.instrument = Instrument.objects.create(
            instrument_token=999000001,
            exchange="NSE",
            symbol="NIFTY",
            trading_symbol="NIFTY 50 TEST",
            instrument_type="IDX",
        )

    def test_resolves_pending_forecast_from_first_completed_one_minute_candle(self):
        now = timezone.now().replace(second=0, microsecond=0)
        target = now - timedelta(minutes=5)
        candle_time = target + timedelta(minutes=1)
        session = AnalysisSession.objects.create(
            instrument=self.instrument,
            session_type="MARKET_ANALYSIS",
            status="COMPLETE",
            timeframe="15m",
            parsed_output={
                "probability": {
                    "upside_pct": 50,
                    "downside_pct": 30,
                    "sideways_pct": 20,
                }
            },
            forecast_horizon_minutes=15,
            forecast_anchor_price=Decimal("100.00"),
            forecast_target_time=target,
            forecast_sideways_band_pct=Decimal("0.050"),
            forecast_outcome_status="PENDING",
            probability_method_version="horizon-base-rate-v1",
        )
        Candle.objects.create(
            instrument=self.instrument,
            timeframe="1m",
            candle_time=candle_time,
            open=Decimal("100.00"),
            high=Decimal("101.00"),
            low=Decimal("99.90"),
            close=Decimal("100.20"),
            volume=100,
            source="ZERODHA",
        )

        with patch(
            "apps.ai_engine.services.forecast_outcome_service.timezone.now",
            return_value=now,
        ):
            result = ForecastOutcomeService.resolve_due_forecasts()

        session.refresh_from_db()
        self.assertEqual(result, {"checked": 1, "resolved": 1})
        self.assertEqual(session.forecast_outcome_status, "RESOLVED")
        self.assertEqual(session.forecast_actual_class, "UP")
        self.assertEqual(session.forecast_brier_score, Decimal("0.380000"))
        report = ConfidenceCalibrationService.get_probability_report(
            horizon_minutes=15,
        )
        self.assertEqual(report["sample_size"], 1)
        self.assertEqual(report["mean_brier_score"], 0.38)

    def test_missing_target_candle_eventually_exits_pending_state(self):
        now = timezone.now().replace(second=0, microsecond=0)
        session = AnalysisSession.objects.create(
            instrument=self.instrument,
            session_type="MARKET_ANALYSIS",
            status="COMPLETE",
            timeframe="15m",
            parsed_output={
                "probability": {
                    "upside_pct": 50,
                    "downside_pct": 30,
                    "sideways_pct": 20,
                }
            },
            forecast_horizon_minutes=15,
            forecast_anchor_price=Decimal("100.00"),
            forecast_target_time=now - timedelta(minutes=15),
            forecast_sideways_band_pct=Decimal("0.050"),
            forecast_outcome_status="PENDING",
            probability_method_version="horizon-base-rate-v1",
        )

        with patch(
            "apps.ai_engine.services.forecast_outcome_service.timezone.now",
            return_value=now,
        ):
            ForecastOutcomeService.resolve_due_forecasts()

        session.refresh_from_db()
        self.assertEqual(session.forecast_outcome_status, "INSUFFICIENT_DATA")


class IntradayBaseRateTests(TestCase):
    def test_base_rate_uses_completed_prior_day_one_minute_outcomes(self):
        instrument = self.instrument = Instrument.objects.create(
            instrument_token=999000002,
            exchange="NSE",
            symbol="NIFTY",
            trading_symbol="NIFTY 50 HISTORY TEST",
            instrument_type="IDX",
        )
        ist = ZoneInfo("Asia/Kolkata")
        fixed_now = datetime(2026, 9, 29, 10, 15, 30, tzinfo=ist)
        for days_ago in range(1, 37):
            session_date = (fixed_now - timedelta(days=days_ago)).date()
            start = datetime.combine(session_date, time(10, 15), tzinfo=ist)
            end = datetime.combine(session_date, time(10, 30), tzinfo=ist)
            for candle_time, close in ((start, "100.00"), (end, "100.10")):
                Candle.objects.create(
                    instrument=instrument,
                    timeframe="1m",
                    candle_time=candle_time,
                    open=Decimal("100.00"),
                    high=Decimal("100.20"),
                    low=Decimal("99.90"),
                    close=Decimal(close),
                    volume=100,
                    source="MOCK" if days_ago == 36 else "ZERODHA",
                )

        def localtime(value=None):
            return fixed_now if value is None else value.astimezone(ist)

        with (
            patch(
                "apps.market_data.repositories.instrument_repository.InstrumentRepository.get_by_symbol",
                return_value=instrument,
            ),
            patch(
                "apps.market_data.services.historical_distribution_service.timezone.localtime",
                side_effect=localtime,
            ),
        ):
            from apps.market_data.services.historical_distribution_service import (
                HistoricalDistributionService,
            )

            result = HistoricalDistributionService.intraday_direction_base_rate(
                "NIFTY",
                "15m",
                15,
            )

        self.assertEqual(result["sample_size"], 35)
        self.assertEqual(result["outcome_candle_timeframe"], "1m")
        self.assertEqual(
            result["latest_sample_date"],
            (fixed_now.date() - timedelta(days=1)).isoformat(),
        )
        self.assertEqual(result["upside_pct"], 100.0)
        self.assertEqual(result["downside_pct"], 0.0)
        self.assertEqual(result["sideways_pct"], 0.0)
