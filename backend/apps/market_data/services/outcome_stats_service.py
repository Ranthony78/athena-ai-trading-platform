"""
Aggregates win-rate statistics from resolved AISignal/StrategySignal
outcomes (produced by OutcomeTrackingService).

Win/loss is classified by the REAL points_captured value (> 0 = win),
not by which outcome_status resolved the signal. A SQUARED_OFF or
EXPIRED signal that still ended up net-positive is a real win — using
the outcome_status label alone would repeat the exact gross-vs-net
misclassification found and documented in PaperTrading earlier.
"""
import logging

logger = logging.getLogger(__name__)


class OutcomeStatsService:

    @staticmethod
    def _is_win(points_captured) -> bool:
        return points_captured is not None and points_captured > 0

    @classmethod
    def get_summary(cls, user=None) -> dict:
        """Overall win-rate summary, separately for AI and Strategy signals."""
        from apps.ai_engine.models import AISignal
        from apps.strategies.models import StrategySignal

        results = {}
        for label, model in (("ai_signals", AISignal), ("strategy_signals", StrategySignal)):
            base_qs = model.objects.all()
            if user:
                base_qs = base_qs.filter(user=user)

            open_count = base_qs.filter(outcome_status="OPEN").count()
            resolved = list(
                base_qs.exclude(outcome_status="OPEN").values(
                    "points_captured", "points_captured_pct", "outcome_status", "product"
                )
            )

            total = len(resolved)
            wins = sum(1 for r in resolved if cls._is_win(r["points_captured"]))
            losses = total - wins
            win_rate = round(wins / total * 100, 2) if total else None

            valid_pcts = [
                float(r["points_captured_pct"])
                for r in resolved if r["points_captured_pct"] is not None
            ]
            avg_points_pct = round(sum(valid_pcts) / len(valid_pcts), 2) if valid_pcts else None

            by_outcome_status = {
                status: sum(1 for r in resolved if r["outcome_status"] == status)
                for status in ("TARGET_HIT", "STOP_HIT", "SQUARED_OFF", "EXPIRED")
            }

            by_product = {}
            for product in ("MIS", "NRML"):
                prod_rows = [r for r in resolved if r["product"] == product]
                prod_wins = sum(1 for r in prod_rows if cls._is_win(r["points_captured"]))
                by_product[product] = {
                    "total": len(prod_rows),
                    "wins": prod_wins,
                    "win_rate": round(prod_wins / len(prod_rows) * 100, 2) if prod_rows else None,
                }

            results[label] = {
                "open": open_count,
                "total_resolved": total,
                "wins": wins,
                "losses": losses,
                "win_rate": win_rate,
                "avg_points_captured_pct": avg_points_pct,
                "by_outcome_status": by_outcome_status,
                "by_product": by_product,
            }

        return results

    @classmethod
    def get_by_strategy(cls, user=None) -> list[dict]:
        """Win rate per strategy (StrategySignal only)."""
        from apps.strategies.models import StrategySignal, Strategy

        qs = StrategySignal.objects.exclude(outcome_status="OPEN")
        if user:
            qs = qs.filter(user=user)

        rows = []
        for strategy in Strategy.objects.all():
            sigs = list(qs.filter(strategy=strategy).values("points_captured"))
            total = len(sigs)
            if total == 0:
                continue
            wins = sum(1 for s in sigs if cls._is_win(s["points_captured"]))
            rows.append({
                "strategy_id": strategy.id,
                "strategy_name": strategy.name,
                "total": total,
                "wins": wins,
                "losses": total - wins,
                "win_rate": round(wins / total * 100, 2),
            })
        return sorted(rows, key=lambda r: -r["total"])

    @classmethod
    def get_by_symbol(cls, user=None) -> list[dict]:
        """Win rate per underlying symbol, combining AI and Strategy signals."""
        from apps.ai_engine.models import AISignal
        from apps.strategies.models import StrategySignal

        combined: dict[str, list] = {}
        for model in (AISignal, StrategySignal):
            qs = model.objects.exclude(outcome_status="OPEN").select_related("instrument")
            if user:
                qs = qs.filter(user=user)
            for sig in qs:
                combined.setdefault(sig.instrument.symbol, []).append(sig.points_captured)

        rows = []
        for symbol, points_list in combined.items():
            total = len(points_list)
            wins = sum(1 for p in points_list if cls._is_win(p))
            rows.append({
                "symbol": symbol,
                "total": total,
                "wins": wins,
                "losses": total - wins,
                "win_rate": round(wins / total * 100, 2) if total else None,
            })
        return sorted(rows, key=lambda r: -r["total"])