# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scan_manager', '0002_auto_20151221_2352'),
    ]

    operations = [
        migrations.AddField(
            model_name='host',
            name='data',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='host',
            name='hostname',
            field=models.TextField(),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='host',
            name='ip',
            field=models.TextField(),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='host',
            name='ip_host',
            field=models.TextField(),
            preserve_default=True,
        ),
    ]
