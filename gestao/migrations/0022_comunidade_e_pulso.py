from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies=[('gestao','0021_ux_operacional')]
    operations=[
      migrations.CreateModel(name='PublicacaoComunidade',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('criado_em',models.DateTimeField(auto_now_add=True)),('atualizado_em',models.DateTimeField(auto_now=True)),('texto',models.CharField(max_length=500)),('ativo',models.BooleanField(default=True)),('autor',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='publicacoes_comunidade',to='gestao.colaborador')),('loja',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='lojas.loja'))]),
      migrations.CreateModel(name='PulsoColaborador',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('criado_em',models.DateTimeField(auto_now_add=True)),('atualizado_em',models.DateTimeField(auto_now=True)),('humor',models.CharField(choices=[('bem','Bem'),('normal','Normal'),('cansado','Cansado'),('motivado','Motivado')],max_length=20)),('comentario',models.CharField(blank=True,max_length=240)),('data',models.DateField(default=django.utils.timezone.localdate)),('colaborador',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='pulsos',to='gestao.colaborador')),('loja',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='lojas.loja'))],options={'unique_together':{('colaborador','data')}}),
    ]
