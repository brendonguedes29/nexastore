from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[('gestao','0018_etapatreinamento_questoes')]
    operations=[migrations.AddField(model_name='etapatreinamento',name='slides',field=models.JSONField(blank=True,default=list))]
