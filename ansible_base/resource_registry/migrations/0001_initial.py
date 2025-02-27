# Generated by Django 4.2.6 on 2024-01-19 20:06

import uuid

import django.db.models.deletion
from django.db import migrations, models

import ansible_base.resource_registry.models.resource


def create_service_id(apps, schema_editor):
    ServiceID = apps.get_model("dab_resource_registry", "ServiceID")
    if not ServiceID.objects.exists():
        ServiceID.objects.create()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceID',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ],
        ),
        migrations.RunPython(
            code=create_service_id,
            reverse_code=migrations.RunPython.noop
        ),
        migrations.CreateModel(
            name='ResourceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('externally_managed', models.BooleanField()),
                ('migrated', models.BooleanField(default=False)),
                ('name', models.CharField(db_index=True, editable=False, max_length=256, unique=True)),
                ('content_type', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE, related_name='resource_type', to='contenttypes.contenttype')),
            ],
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.TextField()),
                ('service_id', models.CharField(default=ansible_base.resource_registry.models.resource.short_service_id, max_length=8)),
                ('resource_id', models.UUIDField(db_index=True, default=uuid.uuid4, unique=True)),
                ('name', models.CharField(max_length=512, null=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='contenttypes.contenttype')),
            ],
            options={
                'indexes': [models.Index(fields=['content_type', 'object_id'], name='dab_resourc_content_6d9d9c_idx')],
                'unique_together': {('content_type', 'object_id')},
            },
        ),
    ]
