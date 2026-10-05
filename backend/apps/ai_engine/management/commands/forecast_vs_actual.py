"""
Compare each saved NEXT_SESSION outlook with what the market then did.

    python manage.py forecast_vs_actual [--days 10]

For every saved outlook, the "actual" session is the first trading day after
the outlook was created. Only real stored daily candles are used; if that
day's candle is not stored yet the outlook is shown as pending.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.ai_engine.models import AnalysisSession
from apps.market_data.models import Candle


class Command(BaseCommand):
    help = "Show saved next-session outlooks next to the actual following session."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=10)

    def handle(self, *args, **options):
        since = timezone.now() - timedelta(days=options["days"])
        sessions = (
            AnalysisSession.objects.filter(
                market_context__analysis_mode="NEXT_SESSION",
                status="COMPLETE",
                created_at__gte=since,
            )
            .select_related("instrument")
            .order_by("created_at")
        )
        if not sessions:
            self.stdout.write("No saved next-session outlooks in that period.")
            return
        for s in sessions:
            made = timezone.localtime(s.created_at)
            out = s.parsed_output or {}
            prob = out.get("probability") or {}
            self.stdout.write(
                f"\n{s.instrument.symbol} outlook saved {made:%a %d %b %H:%M}"
                f" | signal {out.get('signal')} | confidence {out.get('confidence_level')}"
            )
            view = out.get("market_view")
            if view:
                self.stdout.write(f"  view: {str(view)[:200]}")
            if prob.get("upside_pct") is not None:
                self.stdout.write(
                    f"  base rate: up {prob['upside_pct']}% / down {prob['downside_pct']}%"
                    f" / sideways {prob['sideways_pct']}% (n={prob.get('sample_size')})"
                )
            nxt = (
                Candle.objects.filter(
                    instrument=s.instrument,
                    timeframe="1d",
                    candle_time__date__gt=made.date(),
                )
                .order_by("candle_time")
                .first()
            )
            if nxt is None:
                self.stdout.write("  actual: pending (next session not stored yet)")
                continue
            prev = (
                Candle.objects.filter(
                    instrument=s.instrument,
                    timeframe="1d",
                    candle_time__date__lte=made.date(),
                )
                .order_by("-candle_time")
                .first()
            )
            o, h, lo, c = (
                float(nxt.open),
                float(nxt.high),
                float(nxt.low),
                float(nxt.close),
            )
            gap = (o - float(prev.close)) / float(prev.close) * 100 if prev else 0.0
            self.stdout.write(
                f"  actual {timezone.localtime(nxt.candle_time):%a %d %b}: "
                f"O {o:.2f} H {h:.2f} L {lo:.2f} C {c:.2f} | gap {gap:+.2f}% "
                f"| open->close {(c - o) / o * 100:+.2f}% | range {(h - lo) / o * 100:.2f}%"
            )
