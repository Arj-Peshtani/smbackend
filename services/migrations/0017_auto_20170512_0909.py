# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-12 06:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0016_auto_20170512_0204"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Service",
            new_name="OntologyWord",
        ),
    ]
