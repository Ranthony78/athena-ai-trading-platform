"""
backend/apps/ai_engine/services/confidence_calibration_service.py

New file.

This is the actual answer to "does the AI learn by checking probability
against actual results" — Level 2 statistical learning per the project's
own AI-learning design doc. Claude itself never retrains; this computes
real calibration statistics in Django from completed AISignal outcomes,
comparing what Claude SAID (confidence_score) against what REALLY
happened (points_captured from OutcomeTrackingService).

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
    Computes real calibration statistics: for each confidence band
    Claude has actually used, what fraction of those signals were
    genuinely profitable once outcome-tracked?
    """

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