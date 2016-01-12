# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('scan_manager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='host',
            name='ctime',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2015, 12, 21, 23, 52, 13, 210155, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='host',
            name='mtime',
            field=models.DateTimeField(default=datetime.datetime(2015, 12, 21, 23, 52, 20, 552030, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
