# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scan_manager', '0005_auto_20151225_1547'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='ip',
            field=models.IPAddressField(unique=True),
            preserve_default=True,
        ),
    ]
