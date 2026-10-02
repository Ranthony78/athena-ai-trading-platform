from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market_data", "0004_candle_source_provenance"),
    ]

    operations = [
        migrations.AlterField(
            model_name="instrument",
            name="exchange",
            field=models.CharField(
                choices=[
                    ("NSE", "NSE"),
                    ("BSE", "BSE"),
                    ("NFO", "NFO"),
                    ("CDS", "CDS"),
                    ("MCX", "MCX"),
                ],
                db_index=True,
                max_length=10,
            ),
        ),
    ]
