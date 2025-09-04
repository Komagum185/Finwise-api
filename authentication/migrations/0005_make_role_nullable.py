# Manual migration to fix role column constraint
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_add_flexible_roles'),
    ]

    operations = [
        # Make the old role column nullable to prevent constraint errors
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Admin'), 
                    ('staff', 'Staff'), 
                    ('mse', 'MSE'), 
                    ('partner', 'Partner')
                ], 
                max_length=10, 
                null=True, 
                blank=True,
                help_text='Legacy role field - use new boolean role fields instead'
            ),
        ),
    ]
