from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[('gestao','0020_tentativas_avaliacao')]
    operations=[
        migrations.AddField(model_name='auditoria',name='inicio',field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name='auditoria',name='previsao_conclusao',field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name='auditoria',name='conclusao',field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name='documentogestao',name='status',field=models.CharField(choices=[('rascunho','Rascunho'),('aprovacao','Em aprovação'),('vigente','Vigente'),('obsoleto','Obsoleto')],default='rascunho',max_length=20)),
        migrations.AddField(model_name='documentogestao',name='data_emissao',field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name='registroproducao',name='equipamento',field=models.CharField(blank=True,max_length=120)),
        migrations.AddField(model_name='registroproducao',name='produto',field=models.CharField(blank=True,max_length=120)),
        migrations.AddField(model_name='registroproducao',name='turno',field=models.CharField(blank=True,max_length=80)),
    ]
