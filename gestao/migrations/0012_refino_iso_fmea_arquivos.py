from django.db import migrations, models
import cloudinary_storage.storage

class Migration(migrations.Migration):
    dependencies=[('gestao','0011_etapas_cronograma_qualidade')]
    operations=[
        migrations.AlterField(model_name='documentogestao',name='arquivo',field=models.FileField(blank=True,null=True,storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),upload_to='gestao/documentos/')),
        migrations.AlterField(model_name='requisitoiso',name='norma',field=models.CharField(default='ISO 9001:2026',max_length=40)),
        migrations.AddField(model_name='requisitoiso',name='orientacao',field=models.TextField(blank=True)),
        migrations.AddField(model_name='requisitoiso',name='observacoes',field=models.TextField(blank=True)),
        migrations.AddField(model_name='requisitoiso',name='prazo',field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name='requisitoiso',name='evidencia_arquivo',field=models.FileField(blank=True,null=True,storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),upload_to='gestao/iso_evidencias/')),
        migrations.AddField(model_name='riscofmea',name='controles_atuais',field=models.TextField(blank=True)),
        migrations.AddField(model_name='riscofmea',name='responsavel_acao',field=models.CharField(blank=True,max_length=120)),
        migrations.AddField(model_name='riscofmea',name='prazo_acao',field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name='riscofmea',name='status_acao',field=models.CharField(choices=[('aberta','Aberta'),('andamento','Em andamento'),('concluida','Concluída')],default='aberta',max_length=20)),
        migrations.AddField(model_name='riscofmea',name='severidade_pos',field=models.PositiveSmallIntegerField(blank=True,null=True)),
        migrations.AddField(model_name='riscofmea',name='ocorrencia_pos',field=models.PositiveSmallIntegerField(blank=True,null=True)),
        migrations.AddField(model_name='riscofmea',name='deteccao_pos',field=models.PositiveSmallIntegerField(blank=True,null=True)),
        migrations.AlterField(model_name='etapatreinamento',name='material',field=models.FileField(blank=True,null=True,storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),upload_to='gestao/treinamentos/')),
    ]
