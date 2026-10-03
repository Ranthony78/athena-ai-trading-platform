from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.market_data.models import Instrument

from .services.volatility_setup_service import VolatilitySetupService


@override_settings(MARKET_PROVIDER="zerodha")
class VolatilitySetupServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="straddle-test", password="not-a-real-password"
        )
        self.expiry = date.today() + timedelta(days=7)
        self.call = self._instrument("NIFTYTESTCE", 880001, "CE")
        self.put = self._instrument("NIFTYTESTPE", 880002, "PE")
        now = timezone.now().isoformat()
        self.context = {
            "symbol": "NIFTY",
            "analysis_mode": "LIVE",
            "forecast_horizon_minutes": 15,
            "quote_source": "ZERODHA",
            "session": {"is_live": True},
            "quote": {"ltp": 22400, "timestamp": now},
            "vix": {"ltp": 14, "timestamp": now},
            "options": {
                "symbol": "NIFTY",
                "atm_strike": 22400,
                "expiry": self.expiry.isoformat(),
                "atm_call": self._row("NIFTYTESTCE", "CE", now),
                "atm_put": self._row("NIFTYTESTPE", "PE", now),
            },
            "rule_evidence": {
                "as_of": now,
                "expected_move": {"horizon_minutes": 15, "one_sigma_points": 250},
                "volatility_context": {
                    "status": "available",
                    "ratio": 1.2,
                    "sample_size": 30,
                },
            },
            "market_drivers": {"event_calendar": {"status": "unavailable"}},
        }

    def _instrument(self, trading_symbol, token, option_type):
        return Instrument.objects.create(
            instrument_token=token,
            exchange="NFO",
            symbol="NIFTY",
            trading_symbol=trading_symbol,
            instrument_type=option_type,
            option_type=option_type,
            strike=Decimal("22400"),
            expiry=self.expiry,
            lot_size=75,
        )

    @staticmethod
    def _row(symbol, option_type, now):
        return {
            "trading_symbol": symbol,
            "option_type": option_type,
            "strike": 22400,
            "expiry": date.today().isoformat(),
            "ltp": 100,
            "lot_size": 75,
            "quote_timestamp": now,
            "best_bid": 99,
            "best_ask": 101,
        }

    def test_mismatched_horizon_blocks_candidate_without_crashing(self):
        self.context["rule_evidence"]["expected_move"]["horizon_minutes"] = 30
        result = VolatilitySetupService.build_candidate(
            parsed={"risks": []}, context=self.context, user=self.user
        )
        self.assertFalse(result["eligible"])

    def test_eligible_candidate_contains_both_atm_contracts_and_combined_risk(self):
        self.context["options"]["atm_call"]["expiry"] = self.expiry.isoformat()
        self.context["options"]["atm_put"]["expiry"] = self.expiry.isoformat()

        result = VolatilitySetupService.build_candidate(
            parsed={"risks": []}, context=self.context, user=self.user
        )

        self.assertTrue(result["eligible"])
        self.assertEqual({leg["option_type"] for leg in result["legs"]}, {"CE", "PE"})
        self.assertEqual(result["combined_premium_per_unit"], 202)
        self.assertEqual(result["maximum_loss_per_lot_before_taxes"], 15150)
        self.assertTrue(result["paper_only"])

    def test_low_relative_volatility_and_combined_premium_hurdle_block_candidate(self):
        self.context["options"]["atm_call"]["expiry"] = self.expiry.isoformat()
        self.context["options"]["atm_put"]["expiry"] = self.expiry.isoformat()
        self.context["rule_evidence"]["volatility_context"]["ratio"] = 0.8
        self.context["rule_evidence"]["expected_move"]["one_sigma_points"] = 100

        result = VolatilitySetupService.build_candidate(
            parsed={"risks": []}, context=self.context, user=self.user
        )

        self.assertFalse(result["eligible"])
        self.assertEqual(result["legs"], [])
        self.assertTrue(
            any("relative volatility" in reason.lower() for reason in result["reasons"])
        )
        self.assertTrue(
            any(
                "combined-premium hurdle" in reason.lower()
                for reason in result["reasons"]
            )
        )

    def test_high_event_risk_and_wide_spread_block_candidate(self):
        for row in (
            self.context["options"]["atm_call"],
            self.context["options"]["atm_put"],
        ):
            row["expiry"] = self.expiry.isoformat()
            row["best_bid"] = 80
            row["best_ask"] = 120

        result = VolatilitySetupService.build_candidate(
            parsed={"risks": ["High event risk: verified policy announcement today"]},
            context=self.context,
            user=self.user,
        )

        self.assertFalse(result["eligible"])
        self.assertTrue(
            any("event risk" in reason.lower() for reason in result["reasons"])
        )
        self.assertTrue(any("spread" in reason.lower() for reason in result["reasons"]))

    def test_stale_quotes_block_candidate(self):
        old = (timezone.now() - timedelta(minutes=5)).isoformat()
        for row in (
            self.context["options"]["atm_call"],
            self.context["options"]["atm_put"],
        ):
            row["expiry"] = self.expiry.isoformat()
            row["quote_timestamp"] = old

        result = VolatilitySetupService.build_candidate(
            parsed={"risks": []}, context=self.context, user=self.user
        )

        self.assertFalse(result["eligible"])
        self.assertTrue(any("two minutes" in reason for reason in result["reasons"]))
