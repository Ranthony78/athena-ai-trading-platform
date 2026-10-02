from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market_data", "0003_alter_instrument_options_instrument_instrument_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="candle",
            name="source",
            field=models.CharField(
                choices=[
                    ("UNKNOWN", "Unknown / legacy"),
                    ("ZERODHA", "Zerodha"),
                    ("MOCK", "Mock provider"),
                    ("SYNTHETIC", "Synthetic test data"),
                ],
                db_index=True,
                default="UNKNOWN",
                max_length=12,
            ),
        ),
    ]
