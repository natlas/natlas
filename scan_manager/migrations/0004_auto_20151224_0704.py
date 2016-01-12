# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scan_manager', '0003_auto_20151222_0000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='ip',
            field=models.IPAddressField(),
            preserve_default=True,
        ),
    ]
