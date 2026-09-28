from tortoise import migrations
from tortoise.migrations import operations as ops

class Migration(migrations.Migration):
    dependencies = [('models', '0002_auto_20260927_1659')]

    initial = False

    operations = [
        ops.RenameField(
            model_name='Sequence',
            old_name='sending_bcc',
            new_name='email_bcc',
        ),
        ops.RenameField(
            model_name='Sequence',
            old_name='sending_daily_max',
            new_name='email_daily_max',
        ),
        ops.RenameField(
            model_name='Sequence',
            old_name='sending_token',
            new_name='email_token',
        ),
        ops.RenameField(
            model_name='Sequence',
            old_name='schedule_days',
            new_name='send_days',
        ),
        ops.RenameField(
            model_name='Sequence',
            old_name='schedule_from',
            new_name='send_time_from',
        ),
        ops.RenameField(
            model_name='Sequence',
            old_name='schedule_to',
            new_name='send_time_to',
        ),
    ]
