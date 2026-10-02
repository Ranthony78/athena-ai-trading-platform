"""Resolve horizon-defined AI price forecasts from stored completed candles."""

from datetime import timedelta

from django.utils import timezone


class ForecastOutcomeService:
    MISSING_CANDLE_GRACE_MINUTES = 10

    @classmethod
    def resolve_due_forecasts(cls) -> dict:
        from apps.ai_engine.models import AnalysisSession
        from apps.market_data.models import Candle

        now = timezone.now()
        pending = AnalysisSession.objects.filter(
            status="COMPLETE",
            forecast_outcome_status="PENDING",
            forecast_target_time__lte=now,
            forecast_anchor_price__isnull=False,
        ).select_related("instrument")
        checked = resolved = 0

        for session in pending.iterator():
            checked += 1
            if not session.instrument_id:
                continue

            target = session.forecast_target_time
            # Historical candles are stored with their interval start. Select
            # the first interval beginning at/after target, as the previous
            # contract did, and allow one forming minute before resolving.
            candle = Candle.objects.filter(
                instrument=session.instrument,
                timeframe="1m",
                source="ZERODHA",
                candle_time__gte=target,
                candle_time__lte=min(target + timedelta(minutes=5), now - timedelta(minutes=1)),
            ).order_by("candle_time").first()
            if not candle:
                if now > target + timedelta(minutes=cls.MISSING_CANDLE_GRACE_MINUTES):
                    session.forecast_outcome_status = "INSUFFICIENT_DATA"
                    session.save(update_fields=["forecast_outcome_status", "updated_at"])
                continue

            anchor = float(session.forecast_anchor_price)
            outcome_price = float(candle.close)
            if anchor <= 0:
                session.forecast_outcome_status = "INSUFFICIENT_DATA"
                session.save(update_fields=["forecast_outcome_status", "updated_at"])
                continue

            move_pct = (outcome_price - anchor) / anchor * 100
            band = float(session.forecast_sideways_band_pct)
            actual_class = "UP" if move_pct > band else "DOWN" if move_pct < -band else "SIDEWAYS"

            probability = (session.parsed_output or {}).get("probability") or {}
            probability_by_class = {
                "UP": probability.get("upside_pct"),
                "DOWN": probability.get("downside_pct"),
                "SIDEWAYS": probability.get("sideways_pct"),
            }
            from .learning_service import LearningService
            probabilities = LearningService._probability(session)
            brier = sum((p - float(label == actual_class)) ** 2 for p, label in zip(probabilities, ("UP", "DOWN", "SIDEWAYS"))) if probabilities else None
            session.forecast_actual_class = actual_class
            session.forecast_outcome_price = candle.close
            session.forecast_resolved_at = candle.candle_time + timedelta(minutes=1)
            session.forecast_brier_score = round(brier, 6) if brier is not None else None
            session.forecast_outcome_status = "RESOLVED"
            session.save(update_fields=[
                "forecast_actual_class", "forecast_outcome_price", "forecast_resolved_at",
                "forecast_brier_score", "forecast_outcome_status", "updated_at",
            ])
            resolved += 1

        return {"checked": checked, "resolved": resolved}
