# Generated manually for flexible role system

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_customuser_rights_alter_customuser_role'),
    ]

    operations = [
        # Add new boolean role fields
        migrations.AddField(
            model_name='customuser',
            name='is_super_admin',
            field=models.BooleanField(default=False, help_text='Full system access'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='is_agent',
            field=models.BooleanField(default=False, help_text='Can manage assigned MSEs'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='is_mse',
            field=models.BooleanField(default=False, help_text='Micro/Small Enterprise user'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='is_partner',
            field=models.BooleanField(default=False, help_text='Partner institution user'),
        ),
        
        # Add new business fields
        migrations.AddField(
            model_name='customuser',
            name='mse_name',
            field=models.CharField(blank=True, help_text='MSE name if user is MSE', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='partner_institution',
            field=models.CharField(blank=True, help_text='Institution name if user is Partner', max_length=100, null=True),
        ),
        
        # Add capabilities field
        migrations.AddField(
            model_name='customuser',
            name='capabilities',
            field=models.JSONField(blank=True, default=list, help_text='List of user capabilities'),
        ),
        
        # Add assigned_agent field (self-referencing foreign key)
        migrations.AddField(
            model_name='customuser',
            name='assigned_agent',
            field=models.ForeignKey(blank=True, help_text='Agent assigned to this user', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_users', to='authentication.customuser'),
        ),
    ]
