from django.db import migrations, models
import cloudinary_storage.storage

class Migration(migrations.Migration):
    dependencies=[('gestao','0015_projetoqualidade_criado_por')]
    operations=[
        migrations.AddField(model_name='treinamento',name='emitir_certificado',field=models.BooleanField(default=True)),
        migrations.AddField(model_name='treinamento',name='certificado_empresa',field=models.FileField(blank=True,null=True,storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),upload_to='gestao/certificados_empresa/')),
        migrations.AddField(model_name='etapatreinamento',name='tipo',field=models.CharField(choices=[('texto','Conteúdo / texto'),('slide','Slide'),('youtube','Vídeo do YouTube'),('video','Vídeo enviado'),('quiz','Quiz'),('atividade','Atividade'),('material','Material / arquivo'),('avaliacao','Avaliação final')],default='texto',max_length=20)),
        migrations.AddField(model_name='etapatreinamento',name='video_arquivo',field=models.FileField(blank=True,null=True,storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),upload_to='gestao/videos_treinamento/')),
        migrations.AddField(model_name='etapatreinamento',name='alternativas',field=models.JSONField(blank=True,default=list)),
        migrations.AddField(model_name='etapatreinamento',name='explicacao',field=models.TextField(blank=True)),
        migrations.AddField(model_name='etapatreinamento',name='nota_minima',field=models.PositiveSmallIntegerField(default=70)),
    ]
