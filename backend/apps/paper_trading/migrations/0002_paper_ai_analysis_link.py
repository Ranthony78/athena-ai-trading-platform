import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_engine", "0004_analysis_forecast_tracking"),
        ("paper_trading", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="paperorder",
            name="analysis_session",
            field=models.ForeignKey(
                blank=True,
                help_text="AI forecast that led to this paper-only order, when applicable.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="paper_orders",
                to="ai_engine.analysissession",
            ),
        ),
        migrations.AddField(
            model_name="paperposition",
            name="entry_brokerage",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Opening commissions still attributable to this open position.",
                max_digits=10,
            ),
        ),
        migrations.AlterField(
            model_name="papertrade",
            name="position",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="trades",
                to="paper_trading.paperposition",
            ),
        ),
        migrations.AddField(
            model_name="paperposition",
            name="analysis_session",
            field=models.ForeignKey(
                blank=True,
                help_text="AI forecast linked to this position when all opening fills share it.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="paper_positions",
                to="ai_engine.analysissession",
            ),
        ),
        migrations.AddField(
            model_name="papertrade",
            name="analysis_session",
            field=models.ForeignKey(
                blank=True,
                help_text="AI forecast linked to this completed paper trade, when unambiguous.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="paper_trades",
                to="ai_engine.analysissession",
            ),
        ),
    ]
