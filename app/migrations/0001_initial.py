# Generated by Django 5.0.3 on 2024-03-23 10:05

from django.db import migrations, models

import app.models


def create_tables(_, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_machine (
                id INTEGER PRIMARY KEY,
                description VARCHAR(100) NOT NULL
            )
        """,
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_simulation (
                id INTEGER PRIMARY KEY,
                name_description VARCHAR(100) NOT NULL,
                status VARCHAR(10) NOT NULL,
                machine_id INTEGER,
                creation_date TEXT,
                update_date TEXT,
                graph_data JSONB,
                FOREIGN KEY (machine_id) REFERENCES app_machine(id)
            )
        """,
        )

        cursor.execute(
            """
            INSERT INTO app_machine (description) VALUES
                ('Machine 1'),
                ('Machine 2'),
                ('Machine 3');
        """,
        )


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Machine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(max_length=100)),
            ],
            options={
                "abstract": False,
                "managed": False,
            },
            bases=(models.Model, app.models.RestrictedManager),
        ),
        migrations.CreateModel(
            name="Simulation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name_description", models.CharField(max_length=100)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("running", "Running"), ("finished", "Finished")],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("creation_date", models.DateTimeField(auto_now_add=True)),
                ("update_date", models.DateTimeField(auto_now=True)),
                ("machine", models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, to="app.machine")),
                ("graph_data", models.JSONField(blank=True, null=True)),
            ],
            options={
                "abstract": False,
                "managed": False,
            },
            bases=(models.Model, app.models.RestrictedManager),
        ),
        migrations.RunPython(create_tables),
    ]
