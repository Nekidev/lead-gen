from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0001_initial')]

    initial = False

    operations = [
        ops.AddField(
            model_name='EmailAccount',
            name='name',
            field=fields.CharField(max_length=128, db_default=""),
        ),
    ]
