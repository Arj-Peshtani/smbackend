# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-16 15:33
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0021_auto_20170516_1649"),
    ]

    operations = [
        migrations.RenameField(
            model_name="unit", old_name="description_en", new_name="desc_en",
        ),
        migrations.RenameField(
            model_name="unit", old_name="description_fi", new_name="desc_fi",
        ),
        migrations.RenameField(
            model_name="unit", old_name="description_sv", new_name="desc_sv",
        ),
    ]
