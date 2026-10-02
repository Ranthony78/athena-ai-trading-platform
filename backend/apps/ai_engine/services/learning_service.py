"""User-scoped evaluation and retrospective lessons; never modifies live rules."""
from collections import Counter, defaultdict
from datetime import timedelta

from django.utils import timezone

from ..models import AnalysisSession, LearningWorkerState


class LearningService:
    @staticmethod
    def sessions(user, symbol=None, horizon=None):
        rows = AnalysisSession.objects.filter(user=user).select_related("instrument")
        if symbol:
            rows = rows.filter(instrument__symbol=symbol)
        if horizon:
            rows = rows.filter(forecast_horizon_minutes=horizon)
        return rows

    @classmethod
    def lessons(cls, user, symbol, horizon):
        if not user:
            return {"sample_size": 0, "observations": [], "note": "No user-scoped history available."}
        # Outcomes must already be resolved before this prompt is assembled.
        rows = list(cls.sessions(user, symbol, horizon).filter(
            forecast_outcome_status="RESOLVED", forecast_resolved_at__lt=timezone.now(),
        ).order_by("-session_time")[:200])
        groups = defaultdict(list)
        for row in rows:
            decision = (row.parsed_output or {}).get("signal", "NO_SETUP")
            groups[decision].append(row.forecast_actual_class)
        observations = []
        for decision, outcomes in groups.items():
            if len(outcomes) >= 5:
                observations.append({"decision": "No Trade" if decision in ("NO_SETUP", "NEUTRAL", "WATCH") else decision,
                                     "sample_size": len(outcomes), "subsequent_moves": dict(Counter(outcomes))})
        return {"sample_size": len(rows), "observations": observations,
                "note": "Measured retrospective counts, potentially overlapping forecasts. No Trade is not labelled a win/loss. These observations do not change numerical probabilities or trading rules."}

    @staticmethod
    def _probability(row):
        from math import isfinite
        p = (row.parsed_output or {}).get("probability") or {}
        try:
            values = [float(p[key]) / 100 for key in ("upside_pct", "downside_pct", "sideways_pct")]
            return values if all(isfinite(v) and 0 <= v <= 1 for v in values) and abs(sum(values)-1) <= .002 else None
        except (KeyError, TypeError, ValueError):
            return None

    @classmethod
    def candidate(cls, rows):
        """A versioned frequency-calibration candidate with a chronological holdout.

        Only non-overlapping forecasts are used. The holdout starts on a later
        trading day, and training labels must have existed before that cutoff.
        This is an experiment, not an auto-promoted trading/probability model.
        """
        eligible, last_end = [], None
        for row in sorted(rows, key=lambda r: r.session_time):
            if row.probability_method_version != "horizon-base-rate-v1":
                continue
            if not cls._probability(row) or not row.forecast_target_time or not row.forecast_resolved_at:
                continue
            if last_end and row.session_time <= last_end:
                continue
            eligible.append(row)
            last_end = max(row.forecast_target_time, row.forecast_resolved_at)
        empty = {"version": "frequency-calibration-candidate-v1", "status": "collecting", "production_applied": False,
                 "sample_size": len(eligible), "note": "Needs 100 non-overlapping training outcomes and 30 later validation outcomes for this instrument/horizon. Production probabilities remain unchanged."}
        if len(eligible) < 130:
            return empty
        boundary = timezone.localtime(eligible[int(len(eligible)*.7)].session_time).replace(hour=0, minute=0, second=0, microsecond=0)
        train = [r for r in eligible if r.forecast_resolved_at < boundary]
        test = [r for r in eligible if r.session_time >= boundary]
        if len(train) < 100 or len(test) < 30:
            return empty
        labels = ("UP", "DOWN", "SIDEWAYS")
        frequencies = [(sum(r.forecast_actual_class == label for r in train)+1)/(len(train)+3) for label in labels]
        original, candidate = [], []
        for row in test:
            p = cls._probability(row)
            y = [float(row.forecast_actual_class == label) for label in labels]
            original.append(sum((a-b)**2 for a,b in zip(p,y)))
            candidate.append(sum(((a+f)/2-b)**2 for a,f,b in zip(p,frequencies,y)))
        return {**empty, "status": "evaluated", "training_samples": len(train), "validation_samples": len(test),
                "training_cutoff": boundary.isoformat(), "learned_frequencies": dict(zip(labels, frequencies)),
                "baseline_brier": round(sum(original)/len(original),4), "candidate_brier": round(sum(candidate)/len(candidate),4),
                "note": "Fixed 50% blend with training-set class frequencies; later days held out. Lower Brier is better. Repeated dashboard evaluations reuse this holdout. Review and forward paper validation are required before any promotion."}

    @classmethod
    def report(cls, user, symbol=None, horizon=None):
        from apps.paper_trading.models import PaperTrade
        rows = list(cls.sessions(user, symbol, horizon).order_by("-session_time")[:2000])
        resolved = [r for r in rows if r.forecast_outcome_status == "RESOLVED"]
        groups = defaultdict(list)
        for row in resolved:
            output = row.parsed_output if isinstance(row.parsed_output, dict) else {}
            for dimension, value in (("model", f"{row.provider_used}/{row.model_used}"),
                                     ("instrument", row.instrument.symbol if row.instrument else "unknown"),
                                     ("timeframe", row.timeframe), ("market_view", output.get("market_view", "UNCERTAIN")),
                                     ("prompt", row.prompt_version or "legacy")):
                groups[(dimension,value)].append(row)
        breakdown = []
        for (dimension,value), members in groups.items():
            scores = [float(r.forecast_brier_score) for r in members if r.forecast_brier_score is not None]
            directional = [r for r in members if (r.parsed_output or {}).get("signal") in ("BUY","SELL")]
            correct = sum(r.forecast_actual_class == ("UP" if r.parsed_output["signal"] == "BUY" else "DOWN") for r in directional)
            breakdown.append({"dimension": dimension, "value": value, "sample_size": len(members),
                              "directional_samples": len(directional), "direction_accuracy_pct": round(correct/len(directional)*100,1) if directional else None,
                              "brier": round(sum(scores)/len(scores),4) if scores else None, "limited_sample": len(members)<100})
        trades = PaperTrade.objects.filter(account__user=user, analysis_session__isnull=False)
        if symbol: trades = trades.filter(analysis_session__instrument__symbol=symbol)
        if horizon: trades = trades.filter(analysis_session__forecast_horizon_minutes=horizon)
        trade_rows = list(trades.order_by("exit_time", "id").values(
            "net_pnl", "tag", "analysis_session_id", "analysis_session__paper_evaluation", "exit_time",
        ))
        # A straddle is one strategy outcome, not two independent directional
        # wins/losses. Keep incomplete pairs out until the linked session closes.
        pnls = []
        straddle_pnls = defaultdict(float)
        straddle_times = {}
        for trade in trade_rows:
            if trade["tag"] == "AI_PAPER_VOLATILITY":
                state = trade.get("analysis_session__paper_evaluation") or {}
                if state.get("status") == "CLOSED":
                    session_id = trade["analysis_session_id"]
                    straddle_pnls[session_id] += float(trade["net_pnl"])
                    straddle_times[session_id] = max(straddle_times.get(session_id, trade["exit_time"]), trade["exit_time"])
            else:
                pnls.append((trade["exit_time"], float(trade["net_pnl"])))
        pnls.extend((straddle_times[session_id], pnl) for session_id, pnl in straddle_pnls.items())
        pnls.sort(key=lambda item: item[0])
        pnls = [pnl for _, pnl in pnls]
        completed_straddles = list(straddle_pnls.values())
        wins, losses = [p for p in pnls if p > 0], [p for p in pnls if p < 0]
        equity = peak = drawdown = 0
        for pnl in pnls:
            equity += pnl
            peak = max(peak,equity)
            drawdown = max(drawdown,peak-equity)
        heartbeat = LearningWorkerState.objects.filter(name="default").first()
        active = bool(heartbeat and heartbeat.heartbeat_at and heartbeat.heartbeat_at >= timezone.now()-timedelta(minutes=6))
        no_trade = [r for r in resolved if (r.parsed_output if isinstance(r.parsed_output, dict) else {}).get("signal") in ("NO_SETUP","NEUTRAL","WATCH")]
        return {
            "scope": {"symbol": symbol, "horizon_minutes": horizon, "limit": 2000},
            "counts": dict(Counter(r.forecast_outcome_status for r in rows)), "analyses": len(rows),
            "no_trade": {"resolved": len(no_trade), "subsequent_moves": dict(Counter(r.forecast_actual_class for r in no_trade)),
                         "note": "A later move alone does not prove that taking an option trade would have been profitable."},
            "paper": {"closed_trades":len(pnls),"wins":len(wins),"losses":len(losses),"breakeven":sum(p==0 for p in pnls),
                      "net_pnl":round(sum(pnls),2),"win_rate":round(len(wins)/len(pnls)*100,1) if pnls else None,
                      "average_win":round(sum(wins)/len(wins),2) if wins else None,
                      "average_loss":round(sum(losses)/len(losses),2) if losses else None,"max_drawdown":round(drawdown,2),
                      "closed_straddles":len(completed_straddles),"straddle_net_pnl":round(sum(completed_straddles),2),
                      "note":"AI-linked realized paper fills after recorded simulated costs. Open-position P&L and actual broker charges are excluded."},
            "breakdown": breakdown, "worker": {"active":active,"heartbeat_at":heartbeat.heartbeat_at if heartbeat else None,"result":heartbeat.result if heartbeat else {}},
            "candidate": cls.candidate(resolved) if symbol and horizon else {"status":"select_instrument_and_horizon","production_applied":False},
            "recent": [{"id":r.id,"symbol":r.instrument.symbol if r.instrument else None,"time":r.session_time,"status":r.status,
                        "decision": "No Trade" if (r.parsed_output if isinstance(r.parsed_output, dict) else {}).get("signal") in ("NO_SETUP","NEUTRAL","WATCH") else (r.parsed_output if isinstance(r.parsed_output, dict) else {}).get("signal", "Analysis unavailable"),
                        "reason":(r.parsed_output if isinstance(r.parsed_output, dict) else {}).get("no_trade_reason"),"outcome":r.forecast_actual_class or r.forecast_outcome_status,
                        "paper":r.paper_evaluation,"model":r.model_used,"prompt_version":r.prompt_version} for r in rows[:50]],
        }
