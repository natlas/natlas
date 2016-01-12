# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('ip', models.CharField(max_length=16)),
                ('hostname', models.CharField(max_length=255)),
                ('ip_host', models.CharField(max_length=271)),
                ('ports', models.CommaSeparatedIntegerField(max_length=65535)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
