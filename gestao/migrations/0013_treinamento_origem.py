from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[('gestao','0012_refino_iso_fmea_arquivos')]
    operations=[migrations.AddField(model_name='treinamento',name='origem',field=models.CharField(choices=[('empresa','Empresa'),('nexa','Nexa')],default='empresa',max_length=20))]
