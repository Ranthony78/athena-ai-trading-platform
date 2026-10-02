"""
backend/apps/ai_engine/services/confidence_calibration_service.py

New file.

This service reports Level 2 statistical learning per the project's
AI-learning design. Language models do not retrain here; Django computes
calibration from recorded outcomes so performance can be audited.

Never fabricates: a confidence band with too few completed signals is
flagged low_confidence rather than presented as a trustworthy read. A
"win" is defined as points_captured > 0 (real profit captured) — not
just TARGET_HIT, since a SQUARED_OFF or EXPIRED position can still have
closed profitably.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 10-point-wide confidence bands. Narrower bands give more precise
# calibration but need more data to fill — 10 points is a reasonable
# starting granularity given signal volume is much lower than daily
# candle volume.
CONFIDENCE_BANDS = [
    (0, 39), (40, 49), (50, 59), (60, 69),
    (70, 79), (80, 89), (90, 100),
]

MIN_SAMPLE_FOR_CONFIDENCE = 10  # completed signals per band


class ConfidenceCalibrationService:
    """
    Computes calibration statistics for recorded provider outputs and
    measured outcomes.
    """

    MIN_PROBABILITY_SAMPLE_FOR_CONFIDENCE = 10

    @classmethod
    def get_paper_trade_report(cls, user=None, symbol=None) -> dict:
        """Summarize completed paper trades explicitly linked to AI sessions.

        This is an auditable outcome report, not online model training.
        """
        from apps.paper_trading.models import PaperTrade
        from apps.market_data.repositories.instrument_repository import InstrumentRepository

        queryset = PaperTrade.objects.filter(
            analysis_session__isnull=False,
            analysis_session__status="COMPLETE",
        )
        if user is not None:
            queryset = queryset.filter(analysis_session__user=user)
        if symbol:
            instrument = InstrumentRepository.get_by_symbol(symbol)
            if not instrument:
                return {"sample_size": 0, "note": f"No instrument found for {symbol}."}
            queryset = queryset.filter(analysis_session__instrument=instrument)

        rows = list(queryset.values(
            "position_id", "analysis_session_id", "tag", "net_pnl",
            "analysis_session__paper_evaluation",
        ))
        if not rows:
            return {
                "sample_size": 0,
                "low_confidence": True,
                "note": "No completed paper trades linked to AI analyses yet.",
                "automatic_model_updates": False,
            }
        position_cycles = {}
        straddle_cycles = {}
        for row in rows:
            if row["tag"] == "AI_PAPER_VOLATILITY":
                state = row.get("analysis_session__paper_evaluation") or {}
                if state.get("status") == "CLOSED":
                    session_id = row["analysis_session_id"]
                    straddle_cycles[session_id] = straddle_cycles.get(session_id, 0) + (row["net_pnl"] or 0)
            else:
                position_id = row["position_id"]
                position_cycles[position_id] = position_cycles.get(position_id, 0) + (row["net_pnl"] or 0)
        values = list(position_cycles.values()) + list(straddle_cycles.values())
        if not values:
            return {
                "sample_size": 0,
                "low_confidence": True,
                "note": "No completed paper trade cycles linked to AI analyses yet.",
                "automatic_model_updates": False,
            }
        wins = sum(1 for value in values if value > 0)
        count = len(values)
        return {
            "sample_size": count,
            "low_confidence": count < cls.MIN_PROBABILITY_SAMPLE_FOR_CONFIDENCE,
            "net_win_rate_pct": round(wins / count * 100, 1),
            "mean_net_pnl": round(sum(float(value) for value in values) / count, 2),
            "cumulative_net_pnl": round(sum(float(value) for value in values), 2),
            "min_sample_for_confidence": cls.MIN_PROBABILITY_SAMPLE_FOR_CONFIDENCE,
            "automatic_model_updates": False,
            "note": "Paper-trade performance is reported separately from forecast direction accuracy.",
        }

    @classmethod
    def get_calibration_report(cls, user=None, instrument=None) -> dict:
        from apps.ai_engine.models import AISignal

        qs = AISignal.objects.exclude(outcome_status="OPEN").exclude(
            points_captured__isnull=True
        ).exclude(confidence_score__isnull=True)

        if user:
            qs = qs.filter(user=user)
        if instrument:
            qs = qs.filter(instrument=instrument)

        signals = list(qs.values("confidence_score", "points_captured", "outcome_status"))

        if not signals:
            return {
                "bands": [],
                "overall_sample_size": 0,
                "note": "No completed signals with outcome data yet — nothing to calibrate against.",
            }

        bands_out = []
        for low, high in CONFIDENCE_BANDS:
            in_band = [
                s for s in signals
                if low <= s["confidence_score"] <= high
            ]
            if not in_band:
                bands_out.append({
                    "band": f"{low}-{high}%",
                    "sample_size": 0,
                    "note": "No completed signals in this band yet.",
                })
                continue

            wins = sum(1 for s in in_band if float(s["points_captured"]) > 0)
            sample_size = len(in_band)
            actual_win_rate = round(wins / sample_size * 100, 1)
            avg_stated_confidence = round(
                sum(s["confidence_score"] for s in in_band) / sample_size, 1
            )

            bands_out.append({
                "band": f"{low}-{high}%",
                "sample_size": sample_size,
                "low_confidence": sample_size < MIN_SAMPLE_FOR_CONFIDENCE,
                "avg_stated_confidence": avg_stated_confidence,
                "actual_win_rate_pct": actual_win_rate,
                # Positive = Claude is underconfident in this band (actual
                # results beat what it claimed). Negative = overconfident
                # (claims more certainty than results support).
                "calibration_gap": round(actual_win_rate - avg_stated_confidence, 1),
            })

        return {
            "bands": bands_out,
            "overall_sample_size": len(signals),
            "min_sample_for_confidence": MIN_SAMPLE_FOR_CONFIDENCE,
        }

    @classmethod
    def get_probability_report(cls, user=None, symbol=None, horizon_minutes=None) -> dict:
        """Score saved three-class price forecasts against their later outcomes.

        This is separate from option-trade profitability: it answers whether
        the numeric UP/DOWN/SIDEWAYS probabilities matched the underlying's
        movement over the declared forecast horizon.
        """
        from apps.ai_engine.models import AnalysisSession
        from apps.market_data.repositories.instrument_repository import InstrumentRepository

        queryset = AnalysisSession.objects.filter(
            status="COMPLETE",
            forecast_outcome_status="RESOLVED",
            probability_method_version="horizon-base-rate-v1",
        )
        if user is not None:
            queryset = queryset.filter(user=user)
        if horizon_minutes is not None:
            queryset = queryset.filter(forecast_horizon_minutes=horizon_minutes)
        if symbol:
            instrument = InstrumentRepository.get_by_symbol(symbol)
            if not instrument:
                return {"sample_size": 0, "note": f"No instrument found for {symbol}."}
            queryset = queryset.filter(instrument=instrument)

        rows = list(queryset.values(
            "parsed_output", "forecast_actual_class", "forecast_brier_score",
            "forecast_horizon_minutes",
        ))
        if not rows:
            return {
                "sample_size": 0,
                "low_confidence": True,
                "note": "No resolved horizon-matched forecasts yet. Collect more completed outcomes before judging calibration.",
                "metric": "3-class Brier score (lower is better; uniform baseline 0.667)",
            }

        scores = [float(row["forecast_brier_score"]) for row in rows
                  if row["forecast_brier_score"] is not None]
        correct = 0
        for row in rows:
            probability = (row["parsed_output"] or {}).get("probability") or {}
            values = {
                "UP": probability.get("upside_pct"),
                "DOWN": probability.get("downside_pct"),
                "SIDEWAYS": probability.get("sideways_pct"),
            }
            available = {key: float(value) for key, value in values.items() if value is not None}
            if available and max(available, key=available.get) == row["forecast_actual_class"]:
                correct += 1

        return {
            "sample_size": len(rows),
            "low_confidence": len(rows) < cls.MIN_PROBABILITY_SAMPLE_FOR_CONFIDENCE,
            "horizon_minutes": horizon_minutes,
            "symbol": symbol,
            "mean_brier_score": round(sum(scores) / len(scores), 4) if scores else None,
            "uniform_brier_baseline": 0.6667,
            "top_class_accuracy_pct": round(correct / len(rows) * 100, 1),
            "min_sample_for_confidence": cls.MIN_PROBABILITY_SAMPLE_FOR_CONFIDENCE,
            "metric": "3-class Brier score (lower is better; uniform baseline 0.667)",
        }
