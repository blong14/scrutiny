# Generated by Django 4.0.3 on 2022-03-09 04:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notes", "0002_note_position"),
    ]

    operations = [
        migrations.AlterField(
            model_name="note",
            name="position",
            field=models.JSONField(null=True),
        ),
    ]
