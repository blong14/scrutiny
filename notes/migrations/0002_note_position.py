# Generated by Django 4.0.3 on 2022-03-09 04:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="note",
            name="position",
            field=models.JSONField(default={"x": 0, "y": 0}),
            preserve_default=False,
        ),
    ]
