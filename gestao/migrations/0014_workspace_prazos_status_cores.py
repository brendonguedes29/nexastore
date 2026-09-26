from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[('gestao','0013_treinamento_origem')]
    operations=[
        migrations.AlterField(model_name='notaworkspace',name='cor',field=models.CharField(choices=[('amarelo','Amarelo'),('azul','Azul'),('verde','Verde'),('vermelho','Vermelho'),('cinza','Cinza')],default='amarelo',max_length=20)),
        migrations.AddField(model_name='notaworkspace',name='inicio',field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name='notaworkspace',name='previsao',field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name='notaworkspace',name='status',field=models.CharField(choices=[('aberta','Aberta'),('andamento','Em andamento'),('concluida','Concluída')],default='aberta',max_length=20)),
        migrations.AddField(model_name='notaworkspace',name='concluido_em',field=models.DateTimeField(blank=True,null=True)),
    ]
