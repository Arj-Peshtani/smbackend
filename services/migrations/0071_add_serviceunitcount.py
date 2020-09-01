# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-09-13 07:42
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("munigeo", "0004_building"),
        ("services", "0070_longer_unit_data_source"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceUnitCount",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("count", models.PositiveIntegerField()),
                (
                    "division",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="munigeo.AdministrativeDivision",
                    ),
                ),
                (
                    "division_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="munigeo.AdministrativeDivisionType",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="unit_counts",
                        to="services.Service",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="serviceunitcount",
            unique_together=set([("service", "division")]),
        ),
    ]
