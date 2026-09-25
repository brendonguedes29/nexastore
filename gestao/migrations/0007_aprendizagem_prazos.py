from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[('gestao','0006_trilhas_alertas_papeis')]
    operations=[
        migrations.AddField(model_name='trilhacolaborador',name='inicio',field=models.DateField(blank=True,null=True)),
    ]
