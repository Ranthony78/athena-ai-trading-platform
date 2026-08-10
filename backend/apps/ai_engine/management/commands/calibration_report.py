"""
backend/apps/ai_engine/management/commands/calibration_report.py

New file.

Prints the confidence calibration report to the terminal. Deliberately
not a full dashboard page yet — with near-zero completed signals so far,
a UI page would just be showing empty states. Revisit building a real
page once there's enough data for it to be worth looking at regularly.

Usage:
    python manage.py calibration_report
"""

from django.core.management.base import BaseCommand

from apps.ai_engine.services.confidence_calibration_service import (
    ConfidenceCalibrationService,
)


class Command(BaseCommand):
    help = "Print the AI confidence calibration report (stated confidence vs. actual outcomes)"

    def handle(self, *args, **options):
        report = ConfidenceCalibrationService.get_calibration_report()

        if report["overall_sample_size"] == 0:
            self.stdout.write(self.style.WARNING(report["note"]))
            return

        self.stdout.write(
            f"Overall completed signals: {report['overall_sample_size']}\n"
        )
        self.stdout.write(
            f"{'Band':<10} {'N':<6} {'Avg Stated':<12} {'Actual Win%':<13} {'Gap':<8}"
        )
        self.stdout.write("-" * 55)

        for band in report["bands"]:
            if band["sample_size"] == 0:
                self.stdout.write(f"{band['band']:<10} 0      (no data)")
                continue

            flag = " (low confidence)" if band.get("low_confidence") else ""
            gap = band["calibration_gap"]
            gap_str = f"+{gap}" if gap > 0 else str(gap)

            self.stdout.write(
                f"{band['band']:<10} "
                f"{band['sample_size']:<6} "
                f"{band['avg_stated_confidence']:<12} "
                f"{band['actual_win_rate_pct']:<13} "
                f"{gap_str:<8}{flag}"
            )

        self.stdout.write(
            "\nGap = actual win rate - avg stated confidence. "
            "Positive = underconfident, negative = overconfident."
        )