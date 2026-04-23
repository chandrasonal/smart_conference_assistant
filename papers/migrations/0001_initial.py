from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Conference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('year', models.IntegerField()),
            ],
            options={
                'ordering': ['-year', 'name'],
                'unique_together': {('name', 'year')},
            },
        ),
        migrations.CreateModel(
            name='Paper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500)),
                ('authors', models.TextField()),
                ('abstract', models.TextField()),
                ('doi_url', models.URLField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conference', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='papers',
                    to='papers.conference',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
