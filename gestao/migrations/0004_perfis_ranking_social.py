from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
class Migration(migrations.Migration):
    dependencies=[('gestao','0003_compliance_gamificacao')]
    operations=[
      migrations.AddField(model_name='colaborador',name='foto',field=models.ImageField(blank=True,null=True,upload_to='gestao/perfis/')),
      migrations.AddField(model_name='colaborador',name='bio',field=models.CharField(blank=True,max_length=500)),
      migrations.AddField(model_name='colaborador',name='titulo_perfil',field=models.CharField(blank=True,max_length=120)),
      migrations.AddField(model_name='colaborador',name='perfil_visivel',field=models.BooleanField(default=True)),
      migrations.AddField(model_name='colaborador',name='ranking_visivel',field=models.BooleanField(default=True)),
      migrations.AddField(model_name='colaborador',name='mostrar_conquistas',field=models.BooleanField(default=True)),
      migrations.CreateModel(name='PontuacaoAtividade',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('criado_em',models.DateTimeField(auto_now_add=True)),('atualizado_em',models.DateTimeField(auto_now=True)),('categoria',models.CharField(choices=[('jogo','Jogo'),('qualidade','Ferramenta da qualidade'),('treinamento','Treinamento'),('melhoria','Melhoria contínua'),('reconhecimento','Reconhecimento')],max_length=30)),('ferramenta',models.CharField(blank=True,max_length=60)),('titulo',models.CharField(max_length=180)),('pontos',models.PositiveIntegerField(default=0)),('detalhes',models.JSONField(blank=True,default=dict)),('colaborador',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='pontuacoes_atividade',to='gestao.colaborador')),('loja',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='lojas.loja'))]),
      migrations.CreateModel(name='Reconhecimento',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('criado_em',models.DateTimeField(auto_now_add=True)),('atualizado_em',models.DateTimeField(auto_now=True)),('titulo',models.CharField(max_length=120)),('mensagem',models.CharField(blank=True,max_length=500)),('pontos',models.PositiveIntegerField(default=25)),('colaborador',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='reconhecimentos',to='gestao.colaborador')),('concedido_por',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,to=settings.AUTH_USER_MODEL)),('loja',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='lojas.loja'))]),
    ]
