# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scan_manager', '0004_auto_20151224_0704'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='host',
            name='ip_host',
        ),
        migrations.AddField(
            model_name='host',
            name='country',
            field=models.TextField(default='FAKE'),
            preserve_default=False,
        ),
    ]
