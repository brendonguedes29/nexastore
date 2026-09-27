from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[('gestao','0017_alter_etapatreinamento_pergunta')]
    operations=[migrations.AddField(model_name='etapatreinamento',name='questoes',field=models.JSONField(blank=True,default=list))]
