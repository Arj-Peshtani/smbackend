# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-05-02 14:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0049_rename_to_service_node"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="unit",
            name="data_source_url",
        ),
        migrations.AlterField(
            model_name="unit",
            name="data_source",
            field=models.CharField(max_length=30, null=True),
        ),
    ]
