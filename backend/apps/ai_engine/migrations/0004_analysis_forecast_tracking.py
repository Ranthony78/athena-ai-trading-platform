from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ai_engine", "0003_aisignal_outcome_price_aisignal_outcome_status_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="analysissession",
            name="user",
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="analysis_sessions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="analysissession",
            name="forecast_horizon_minutes",
            field=models.PositiveSmallIntegerField(default=15),
        ),
        migrations.AddField(
            model_name="analysissession",
            name="forecast_anchor_price",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="analysissession",
            name="forecast_target_time",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="analysissession",
            name="forecast_sideways_band_pct",
            field=models.DecimalField(decimal_places=3, default=0.05, max_digits=5),
        ),
        migrations.AddField(
            model_name="analysissession",
            name="forecast_outcome_status",
            field=models.CharField(
                choices=[
                    ("NOT_TRACKED", "Not tracked"),
                    ("PENDING", "Pending"),
                    ("RESOLVED", "Resolved"),
                    ("INSUFFICIENT_DATA", "Insufficient data"),
                ],
                db_index=True,
                default="NOT_TRACKED",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="analysissession",
            name="forecast_actual_class",
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name="analysissession",
            name="forecast_outcome_price",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="analysissession",
            name="forecast_resolved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="analysissession",
            name="forecast_brier_score",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="analysissession",
            name="probability_method_version",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
    ]
