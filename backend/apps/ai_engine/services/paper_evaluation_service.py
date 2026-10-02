"""Paper-only, horizon-bound simulations for directional and paired options."""
import logging
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ..models import AnalysisSession, LearningWorkerState
from apps.market_data.engine.market_state import MarketState
from apps.paper_trading.models import PaperPosition, PaperTrade
from apps.paper_trading.services.order_service import OrderService

logger = logging.getLogger(__name__)


class _PairEntryFailed(Exception):
    pass


class PaperEvaluationService:
    POLICY = {"version": "paper-horizon-v1", "lots": 1, "slippage_bps_each_fill": 10,
              "brokerage_each_fill": 20, "taxes_included": False,
              "exit_rule": "First available fresh quote at/after forecast horizon; delays recorded. No stop or target orders."}
    STRADDLE_POLICY = {"version": "paper-long-straddle-v1", "lots": 1,
                       "slippage_bps_each_fill": 10, "brokerage_each_fill": 20,
                       "taxes_included": False, "live_orders": False,
                       "entry_rule": "Both ATM legs must fill inside one database transaction; a failed leg rolls back the pair.",
                       "exit_rule": "Each open leg is closed from its first fresh quote at/after the forecast horizon. Failed leg exits are retried; partial exits remain visible.",
                       "maximum_loss": "Combined option debit plus simulated brokerage; taxes excluded."}

    @classmethod
    @transaction.atomic
    def start(cls, session_id):
        session = AnalysisSession.objects.select_for_update().select_related("user").get(pk=session_id)
        if session.paper_evaluation.get("status") != "REQUESTED":
            return session.paper_evaluation

        def skip(reason, policy=None):
            session.paper_evaluation = {"status": "SKIPPED", "reason": reason, "policy": policy or cls.POLICY}
            session.save(update_fields=["paper_evaluation"])
            return session.paper_evaluation

        parsed = session.parsed_output or {}
        candidate = parsed.get("volatility_setup") or {}
        if session.status != "COMPLETE":
            return skip("Analysis is not complete.")
        if not session.user_id or not session.forecast_target_time or session.forecast_target_time <= timezone.now():
            return skip("No future, trackable live-market horizon for this analysis.", cls.STRADDLE_POLICY if candidate.get("eligible") else cls.POLICY)
        if not MarketState.session_info().get("is_live"):
            return skip("Market closed; no simulated fill invented.", cls.STRADDLE_POLICY if candidate.get("eligible") else cls.POLICY)
        if not LearningWorkerState.objects.filter(name="default", heartbeat_at__gte=timezone.now()-timedelta(minutes=3)).exists():
            return skip("Paper exit worker is offline. Start the learning worker before requesting another paper evaluation.", cls.STRADDLE_POLICY if candidate.get("eligible") else cls.POLICY)

        if candidate.get("eligible") is True:
            return cls._start_straddle(session, candidate, skip)

        if parsed.get("signal") not in ("BUY", "SELL"):
            reason = parsed.get("no_trade_reason") or "No eligible volatility setup or directional signal; no paper position needed."
            return skip(reason)
        signal = getattr(session, "ai_signal", None)
        contract = signal.option_instrument if signal else None
        if not contract or not contract.is_active or not contract.expiry or contract.expiry < timezone.localdate():
            return skip("No active, unexpired suggested option contract.")
        if PaperPosition.objects.filter(account__user=session.user, instrument=contract, is_open=True).exists():
            return skip("This contract already has an open paper position; its attribution is preserved.")
        service = OrderService(user=session.user)
        service.simulator.slippage_bps = Decimal(str(cls.POLICY["slippage_bps_each_fill"]))
        result = service.place_order(user=session.user, symbol=contract.trading_symbol,
            instrument_id=contract.id, transaction_type="BUY", quantity=max(1, contract.lot_size),
            analysis_session_id=session.id, tag="AI_PAPER_HORIZON")
        session.paper_evaluation = {"status": "OPEN" if result["success"] else "SKIPPED",
            "reason": result["message"], "entry": result, "policy": cls.POLICY,
            "target_time": session.forecast_target_time.isoformat(), "started_at": timezone.now().isoformat()}
        session.save(update_fields=["paper_evaluation"])
        return session.paper_evaluation

    @classmethod
    def _start_straddle(cls, session, candidate, skip):
        from .volatility_setup_service import VolatilitySetupService
        legs = candidate.get("legs") or []
        if len(legs) != 2 or {leg.get("option_type") for leg in legs} != {"CE", "PE"}:
            return skip("The candidate does not contain exactly one CE and one PE leg.", cls.STRADDLE_POLICY)
        if any(VolatilitySetupService._quote_age(leg.get("quote_timestamp"), timezone.now()) is None
               or VolatilitySetupService._quote_age(leg.get("quote_timestamp"), timezone.now()) > VolatilitySetupService.MAX_QUOTE_AGE_SECONDS
               for leg in legs):
            return skip("The pair's option quotes became stale before paper entry.", cls.STRADDLE_POLICY)
        evidence_time = (session.market_context or {}).get("rule_evidence", {}).get("as_of")
        evidence_age = VolatilitySetupService._quote_age(evidence_time, timezone.now())
        if evidence_age is None or evidence_age > VolatilitySetupService.MAX_QUOTE_AGE_SECONDS:
            return skip("The volatility evidence became stale before paper entry.", cls.STRADDLE_POLICY)

        contract_ids = [leg.get("instrument_id") for leg in legs]
        if any(not item for item in contract_ids) or PaperPosition.objects.filter(
            account__user=session.user, instrument_id__in=contract_ids, is_open=True,
        ).exists():
            return skip("A pair contract is missing or already has an open paper position; attribution is preserved.", cls.STRADDLE_POLICY)

        service = OrderService(user=session.user)
        service.simulator.slippage_bps = Decimal(str(cls.STRADDLE_POLICY["slippage_bps_each_fill"]))
        entries = []
        try:
            # A failed second leg rolls back the first simulated order and fill.
            with transaction.atomic():
                for leg in legs:
                    result = service.place_order(
                        user=session.user, symbol=leg["trading_symbol"],
                        instrument_id=leg["instrument_id"], transaction_type="BUY",
                        quantity=int(leg["lot_size"]), analysis_session_id=session.id,
                        tag="AI_PAPER_VOLATILITY",
                    )
                    if not result.get("success"):
                        raise _PairEntryFailed(result.get("message") or "A pair leg did not fill.")
                    entries.append({**result, "option_type": leg["option_type"],
                                    "trading_symbol": leg["trading_symbol"]})
        except _PairEntryFailed as exc:
            return skip(f"Both-leg entry cancelled atomically: {exc}", cls.STRADDLE_POLICY)

        actual_debit = sum(float(entry["execution_price"]) * int(entry["filled_quantity"]) for entry in entries)
        actual_brokerage = sum(float(entry.get("brokerage", 0)) for entry in entries)
        session.paper_evaluation = {
            "status": "OPEN", "strategy": "LONG_STRADDLE", "experimental": True,
            "reason": "Both ATM legs filled in paper simulation.", "entries": entries,
            "policy": cls.STRADDLE_POLICY, "target_time": session.forecast_target_time.isoformat(),
            "started_at": timezone.now().isoformat(), "actual_debit": round(actual_debit, 2),
            "brokerage": round(actual_brokerage, 2),
            "maximum_loss_estimate": round(actual_debit + actual_brokerage, 2),
            "taxes_included": False,
            "event_calendar_status": candidate.get("event_calendar_status", "unknown"),
        }
        session.save(update_fields=["paper_evaluation"])
        return session.paper_evaluation

    @classmethod
    @transaction.atomic
    def close_due(cls, session_id):
        session = AnalysisSession.objects.select_for_update().select_related("user").get(pk=session_id)
        state = session.paper_evaluation or {}
        if state.get("strategy") == "LONG_STRADDLE":
            return cls._close_straddle(session, state)
        if state.get("status") not in ("OPEN", "WAITING_EXIT") or not session.forecast_target_time or session.forecast_target_time > timezone.now():
            return
        position = PaperPosition.objects.filter(analysis_session=session, account__user=session.user, is_open=True).select_related("instrument").first()
        if not position:
            state.update(status="CLOSED_EXTERNALLY", reason="Linked paper position was closed or its attribution changed outside this evaluation.")
        elif not MarketState.session_info().get("is_live"):
            state.update(status="WAITING_EXIT", reason="Market closed before a fresh exit quote was available. Exit is delayed; no historical fill fabricated.")
        elif position.instrument.expiry and position.instrument.expiry < timezone.localdate():
            state.update(status="NEEDS_REVIEW", reason="Contract expired before an observable exit. No settlement value fabricated; paper position requires review.")
        else:
            service = OrderService(user=session.user)
            service.simulator.slippage_bps = Decimal(str(state.get("policy", cls.POLICY)["slippage_bps_each_fill"]))
            result = service.place_order(user=session.user, symbol=position.instrument.trading_symbol,
                instrument_id=position.instrument_id, transaction_type="SELL", quantity=position.quantity,
                analysis_session_id=session.id, tag="AI_PAPER_HORIZON_EXIT")
            state.update(status="CLOSED" if result["success"] else "WAITING_EXIT", reason=result["message"],
                         exit=result, exit_delay_seconds=max(0, int((timezone.now()-session.forecast_target_time).total_seconds())))
            if result["success"]:
                trade = PaperTrade.objects.filter(position=position, analysis_session=session).order_by("-id").first()
                if trade:
                    state.update(trade_id=trade.id, net_pnl=float(trade.net_pnl), outcome="WIN" if trade.net_pnl>0 else "LOSS" if trade.net_pnl<0 else "BREAKEVEN")
                    cls.journal(session, trade, state)
        session.paper_evaluation = state
        session.save(update_fields=["paper_evaluation"])

    @classmethod
    def _close_straddle(cls, session, state):
        if state.get("status") not in ("OPEN", "WAITING_EXIT", "PARTIAL_EXIT") or not session.forecast_target_time or session.forecast_target_time > timezone.now():
            return state
        positions = list(PaperPosition.objects.filter(
            analysis_session=session, account__user=session.user, is_open=True,
            tag="AI_PAPER_VOLATILITY",
        ).select_related("instrument"))
        if not positions:
            trades = list(PaperTrade.objects.filter(analysis_session=session, tag="AI_PAPER_VOLATILITY").select_related("instrument").order_by("id"))
            if not trades:
                state.update(status="CLOSED_EXTERNALLY", reason="Neither linked straddle leg remains open; no paired trade record was found.")
            else:
                net_pnl = round(sum(float(trade.net_pnl) for trade in trades), 2)
                state.update(status="CLOSED", net_pnl=net_pnl,
                             outcome="WIN" if net_pnl > 0 else "LOSS" if net_pnl < 0 else "BREAKEVEN",
                             closed_legs=len(trades), exit_delay_seconds=max(0, int((timezone.now()-session.forecast_target_time).total_seconds())))
                for trade in trades:
                    leg_state = {**state, "outcome": "WIN" if trade.net_pnl > 0 else "LOSS" if trade.net_pnl < 0 else "BREAKEVEN"}
                    cls.journal(session, trade, leg_state)
            session.paper_evaluation = state
            session.save(update_fields=["paper_evaluation"])
            return state

        if not MarketState.session_info().get("is_live"):
            state.update(status="WAITING_EXIT", reason="Market closed before fresh leg exits were available. Exit is delayed; no historical fill fabricated.")
        elif any(position.instrument.expiry and position.instrument.expiry < timezone.localdate() for position in positions):
            state.update(status="NEEDS_REVIEW", reason="A straddle leg expired before an observable exit. Remaining exposure is shown for manual review; no settlement value fabricated.")
        else:
            service = OrderService(user=session.user)
            service.simulator.slippage_bps = Decimal(str(state.get("policy", cls.STRADDLE_POLICY)["slippage_bps_each_fill"]))
            exits = state.setdefault("exits", [])
            failed = []
            for position in positions:
                result = service.place_order(user=session.user, symbol=position.instrument.trading_symbol,
                    instrument_id=position.instrument_id, transaction_type="SELL", quantity=position.quantity,
                    analysis_session_id=session.id, tag="AI_PAPER_VOLATILITY_EXIT")
                exits.append({**result, "option_type": position.instrument.option_type,
                              "trading_symbol": position.instrument.trading_symbol})
                if result.get("success"):
                    trade = PaperTrade.objects.filter(position=position, analysis_session=session).order_by("-id").first()
                    if trade:
                        leg_state = {"outcome": "WIN" if trade.net_pnl > 0 else "LOSS" if trade.net_pnl < 0 else "BREAKEVEN",
                                     "exit_delay_seconds": max(0, int((timezone.now()-session.forecast_target_time).total_seconds()))}
                        cls.journal(session, trade, {**state, **leg_state})
                else:
                    failed.append(position.instrument.option_type or position.instrument.trading_symbol)
            still_open = PaperPosition.objects.filter(analysis_session=session, account__user=session.user,
                is_open=True, tag="AI_PAPER_VOLATILITY").exists()
            state["exit_delay_seconds"] = max(0, int((timezone.now()-session.forecast_target_time).total_seconds()))
            if still_open:
                state.update(status="PARTIAL_EXIT" if failed else "WAITING_EXIT",
                             reason="One leg closed; the remaining leg exit will be retried." if failed else "Waiting for the remaining fresh exit fill.",
                             exit_failures=failed)
            else:
                trades = list(PaperTrade.objects.filter(analysis_session=session, tag="AI_PAPER_VOLATILITY"))
                net_pnl = round(sum(float(trade.net_pnl) for trade in trades), 2)
                state.update(status="CLOSED", reason="Both straddle legs have exited.", net_pnl=net_pnl,
                             outcome="WIN" if net_pnl > 0 else "LOSS" if net_pnl < 0 else "BREAKEVEN",
                             closed_legs=len(trades), exit_failures=[])
        session.paper_evaluation = state
        session.save(update_fields=["paper_evaluation"])
        return state

    @staticmethod
    def journal(session, trade, state):
        from apps.journal.models import JournalEntry, TradeNote
        entry, _ = JournalEntry.objects.get_or_create(user=session.user, date=timezone.localdate(trade.exit_time), session="EOD",
            defaults={"title": "Paper evaluation journal"})
        straddle = trade.tag == "AI_PAPER_VOLATILITY"
        TradeNote.objects.get_or_create(trade=trade, defaults={"journal_entry":entry, "instrument":trade.instrument,
            "setup_description": f"AI analysis #{session.id}; {session.prompt_version}; {session.provider_used}/{session.model_used}",
            "entry_reason": "Experimental, volatility-gated ATM CE+PE paper setup." if straddle else "Directional AI view; one-lot long-option simulation.",
            "exit_reason": f"Forecast horizon evaluation; exit delayed by {state.get('exit_delay_seconds', 0)} seconds.",
            "outcome":state["outcome"], "pnl":trade.net_pnl,
            "improvement":"Review both individual legs and combined outcome. A loss alone does not identify a causal mistake. Simulated costs exclude taxes." if straddle else "Review evidence and recorded outcome. A loss alone does not identify a causal mistake. Simulated costs exclude taxes."})
        # Existing user-authored journal prose and summaries are deliberately preserved.
