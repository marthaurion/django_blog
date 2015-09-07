# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0012_auto_20150907_1025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='media',
            name='thumb',
            field=models.ImageField(upload_to='thumbs/%Y/%m/%d', editable=False),
        ),
    ]
