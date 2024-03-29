# Generated by Django 4.1.5 on 2023-01-21 20:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0004_alter_tag_value"),
    ]

    operations = [
        migrations.CreateModel(
            name="JobEvent",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("data", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
